from nltk.corpus import stopwords 
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.cross_validation import KFold
from sklearn.linear_model import Ridge
from scipy.sparse import hstack, csr_matrix
import pandas as pd
import numpy as np
import lightgbm as lgb
import matplotlib.pyplot as plt
import gc, re
from sklearn.utils import shuffle
from contextlib import contextmanager
from sklearn.externals import joblib

debug = False
print("loading data ...")
used_cols = ["item_id", "user_id"]
if debug == False:
    train_df = pd.read_csv("../input/train.csv",  parse_dates = ["activation_date"])
    y = train_df["deal_probability"]
    del train_df["deal_probability"]; gc.collect()
    test_df = pd.read_csv("../input/test.csv",  parse_dates = ["activation_date"])
    # suppl
    train_active = pd.read_csv("../input/train_active.csv", usecols=used_cols)
    test_active = pd.read_csv("../input/test_active.csv", usecols=used_cols)
    train_periods = pd.read_csv("../input/periods_train.csv", parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("../input/periods_test.csv", parse_dates=["date_from", "date_to"])
else:
    train_df = pd.read_csv("../input/train.csv", parse_dates = ["activation_date"])
    train_df = shuffle(train_df, random_state=1234); train_df = train_df.iloc[:50000]
    y = train_df["deal_probability"]
    del train_df["deal_probability"]; gc.collect()
    test_df = pd.read_csv("../input/test.csv",  nrows=1000, parse_dates = ["activation_date"])
    # suppl 
    train_active = pd.read_csv("../input/train_active.csv",  nrows=1000, usecols=used_cols)
    test_active = pd.read_csv("../input/test_active.csv",  nrows=1000, usecols=used_cols)
    train_periods = pd.read_csv("../input/periods_train.csv",  nrows=1000, parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("../input/periods_test.csv",  nrows=1000, parse_dates=["date_from", "date_to"])
print("loading data done!")
# =============================================================================
# Here Based on https://www.kaggle.com/bminixhofer/aggregated-features-lightgbm/code
# =============================================================================

all_samples = pd.concat([train_df,train_active,test_df,test_active]).reset_index(drop=True)
all_samples.drop_duplicates(["item_id"], inplace=True)
del train_active, test_active; gc.collect()

all_periods = pd.concat([train_periods,test_periods])
del train_periods, test_periods; gc.collect()

all_periods["days_up"] = (all_periods["date_to"] - all_periods["date_from"]).dt.days
gp = all_periods.groupby(["item_id"])[["days_up"]]

gp_df = pd.DataFrame()
gp_df["days_up_sum"] = gp.sum()["days_up"]
gp_df["times_put_up"] = gp.count()["days_up"]
gp_df.reset_index(inplace=True)
gp_df.rename(index=str, columns={"index": "item_id"})

all_periods.drop_duplicates(["item_id"], inplace=True)
all_periods = all_periods.merge(gp_df, on="item_id", how="left")
all_periods = all_periods.merge(all_samples, on="item_id", how="left")

gp = all_periods.groupby(["user_id"])[["days_up_sum", "times_put_up"]].mean().reset_index()\
.rename(index=str, columns={"days_up_sum": "avg_days_up_user",
                            "times_put_up": "avg_times_up_user"})

n_user_items = all_samples.groupby(["user_id"])[["item_id"]].count().reset_index() \
.rename(index=str, columns={"item_id": "n_user_items"})
gp = gp.merge(n_user_items, on="user_id", how="left")

del all_samples, all_periods, n_user_items
gc.collect()

train_df = train_df.merge(gp, on="user_id", how="left")
test_df = test_df.merge(gp, on="user_id", how="left")

agg_cols = list(gp.columns)[1:]

del gp; gc.collect()

for col in agg_cols:
    train_df[col].fillna(-1, inplace=True)
    test_df[col].fillna(-1, inplace=True)

print("merging supplimentary data done!")
# =============================================================================
# done! go to the normal steps
# =============================================================================
def rmse(predictions, targets):
    print("calculating RMSE ...")
    return np.sqrt(((predictions - targets) ** 2).mean())

def text_preprocessing1(string):
    '''

    :param string:
    :return:
    '''
    #去掉一些特殊符号
    string=str(string)
    string = string.lower()
    string = re.sub(r'\"', ' ', string)
    string = re.sub(r'\n', ' ', string)
    string = re.sub(r'\t', ' ', string)
    string = re.sub(r'\:', ' ', string)
    string = re.sub(r'\"\"\"\"', ' ', string)
    # string = re.sub(r'_', ' ', string)
    string = re.sub(r'\+', ' ', string)
    string = re.sub(r'\=', ' ', string)
    string = re.sub(r'\,', ' ', string)
    string = re.sub(r'\.', ' ', string)

    string = re.sub(r"(\\u[0-9A-Fa-f]+)", r"", string)

    # https://www.kaggle.com/demery/lightgbm-with-ridge-feature/code
    string = " ".join(map(str.strip, re.split('(\d+)', string)))
    regex = re.compile(u'[^[:alpha:]]')
    string = regex.sub(" ", string)
    string = " ".join(string.split())
    return string

def text_preprocessing(text):        
    text = str(text)
    text = text.lower() 
    # hash words
    text = re.sub(r"(\\u[0-9A-Fa-f]+)",r"", text)
    
    # https://www.kaggle.com/demery/lightgbm-with-ridge-feature/code
    text = " ".join(map(str.strip, re.split('(\d+)',text)))
    regex = re.compile(u'[^[:alpha:]]')
    text = regex.sub(" ", text)
    text = " ".join(text.split())
    return text

@contextmanager
def feature_engineering(df):
    # All the feature engineering here  
    
    def Do_Text_Hash(df):
        print("feature engineering -> hash text ...")
        df["text_feature"] = df.apply(lambda row: " ".join([str(row["param_1"]),
          str(row["param_2"]), str(row["param_3"])]),axis=1)
    
        df["text_feature_2"] = df.apply(lambda row: " ".join([str(row["param_2"]), str(row["param_3"])]),axis=1)        
        df["title_description"] = df.apply(lambda row: " ".join([str(row["title"]), str(row["description"])]),axis=1)
       
        print("feature engineering -> preprocess text ...")       
        df["text_feature"] = df["text_feature"].apply(lambda x: text_preprocessing1(x))
        df["text_feature_2"] = df["text_feature_2"].apply(lambda x: text_preprocessing1(x))
        df["description"] = df["description"].apply(lambda x: text_preprocessing1(x))
        df["title"] = df["title"].apply(lambda x: text_preprocessing1(x))
        df["title_description"] = df["title_description"].apply(lambda x: text_preprocessing1(x))
                       
    def Do_Datetime(df):
        print("feature engineering -> date time ...")
        df["wday"] = df["activation_date"].dt.weekday
#        df["week"] = df["activation_date"].dt.week
#        df["dom"] = df["activation_date"].dt.day
        
    def Do_Label_Enc(df):
        print("feature engineering -> lable encoding ...")
        lbl = LabelEncoder()
        cat_col = ["user_id", "region", "city", "parent_category_name",
               "category_name", "user_type", "image_top_1",
               "param_1", "param_2", "param_3", "image"]
        for col in cat_col:
            df[col] = lbl.fit_transform(df[col].astype(str))
            gc.collect()
    
    import string
    count = lambda l1,l2: sum([1 for x in l1 if x in l2])         
    def Do_NA(df):
        print("feature engineering -> fill na ...")
        df["price"] = np.log(df["price"]+0.001).astype("float32")
        df["price"].fillna(-1,inplace=True)
        df["image_top_1"].fillna("nicapotato",inplace=True)
        df["image"].fillna("noinformation",inplace=True)
        df["param_1"].fillna("nicapotato",inplace=True)
        df["param_2"].fillna("nicapotato",inplace=True)
        df["param_3"].fillna("nicapotato",inplace=True)
        df["title"].fillna("nicapotato",inplace=True)
        df["description"].fillna("nicapotato",inplace=True)
        df['num_desc_punct'] = df['description'].apply(lambda x: count(x, set(string.punctuation)))
             
    def Do_Drop(df):
        df.drop(["activation_date", "item_id"], axis=1, inplace=True)
        
    def Do_Stat_Text(df):
        print("feature engineering -> statistics in text ...")
        textfeats = ["text_feature","text_feature_2","description", "title"]
        for col in textfeats:
            df[col + "_num_chars"] = df[col].apply(len) 
            df[col + "_num_words"] = df[col].apply(lambda comment: len(comment.split()))
            df[col + "_num_unique_words"] = df[col].apply(lambda comment: len(set(w for w in comment.split())))
            df[col + "_words_vs_unique"] = df[col+"_num_unique_words"] / df[col+"_num_words"] * 100
            gc.collect()
                      
    # choose which functions to run
    Do_NA(df)
    Do_Text_Hash(df)    
    Do_Datetime(df)
    Do_Label_Enc(df)
    Do_Stat_Text(df)       
    Do_Drop(df)    
    gc.collect()
    return df

def data_vectorize(df):
    russian_stop = set(stopwords.words("russian"))
    tfidf_para = {
    "stop_words": russian_stop,
    "analyzer": "word",
    "token_pattern": r"\w{1,}",
    "sublinear_tf": True,
    "dtype": np.float32,
    "norm": "l2",
    #"min_df":5,
    #"max_df":.9,
    "smooth_idf":False
    }
    def get_col(col_name): return lambda x: x[col_name]

    vectorizer = FeatureUnion([

        ("description", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=36000,
            **tfidf_para,
            preprocessor=get_col("description"))
         ),
        ("title_description", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=200000,
            **tfidf_para,
            preprocessor=get_col("title_description"))
         ),
        ("text_feature", CountVectorizer(
            ngram_range=(1, 2),
            preprocessor=get_col("text_feature"))
         ),
        ("title", TfidfVectorizer(
            ngram_range=(1, 2),
            **tfidf_para,
            preprocessor=get_col("title"))
         ),
    ])
    vectorizer.fit(df.to_dict("records"))
    ready_full_df = vectorizer.transform(df.to_dict("records"))
    
    tfvocab = vectorizer.get_feature_names()
    
    df.drop(["text_feature", "text_feature_2", "description","title", "title_description"], axis=1, inplace=True)
    df.fillna(-1, inplace=True)     
    return df, ready_full_df, tfvocab

# =============================================================================
# Ridge feature https://www.kaggle.com/demery/lightgbm-with-ridge-feature/code
# =============================================================================
class SklearnWrapper(object):
    def __init__(self, clf, seed=0, params=None, seed_bool = True):
        if(seed_bool == True):
            params['random_state'] = seed
        self.clf = clf(**params)

    def train(self, x_train, y_train):
        self.clf.fit(x_train, y_train)

    def predict(self, x):
        return self.clf.predict(x)

NFOLDS = 10#5
SEED = 42
def get_oof(clf, x_train, y, x_test):
    
    
        
    oof_train = np.zeros((len_train,))
    oof_test = np.zeros((len_test,))
    oof_test_skf = np.empty((NFOLDS, len_test))

    for i, (train_index, test_index) in enumerate(kf):
        print('Ridege oof Fold {}'.format(i))
        x_tr = x_train[train_index]       
        y = np.array(y)
        y_tr = y[train_index]
        x_te = x_train[test_index]      
        clf.train(x_tr, y_tr)       
        oof_train[test_index] = clf.predict(x_te)        
        oof_test_skf[i, :] = clf.predict(x_test)
    oof_test[:] = oof_test_skf.mean(axis=0)
    return oof_train.reshape(-1, 1), oof_test.reshape(-1, 1)


full_df = pd.concat([train_df, test_df])
sub_item_id = test_df["item_id"]
len_train = len(train_df)
len_test = len(test_df)

kf = KFold(len_train, n_folds=NFOLDS, shuffle=True, random_state=SEED)

del train_df, test_df; gc.collect()

feature_engineering(full_df)
full_df, ready_full_df, tfvocab = data_vectorize(full_df)

#'alpha':20.0
ridge_params = {'alpha':20.0, 'fit_intercept':True, 'normalize':False, 'copy_X':True,
                'max_iter':None, 'tol':0.001, 'solver':'auto', 'random_state':SEED}
ridge = SklearnWrapper(clf=Ridge, seed = SEED, params = ridge_params)
ready_df = ready_full_df

# ridge_oof
ridge_oof_train, ridge_oof_test = get_oof(ridge, ready_df[:len_train], y, ready_df[len_train:])
ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
full_df['ridge_preds'] = ridge_preds

print("Modeling Stage ...")
# Combine Dense Features with Sparse Text Bag of Words Features
X = hstack([csr_matrix(full_df.iloc[:len_train]), ready_full_df[:len_train]]) # Sparse Matrix
test = hstack([csr_matrix(full_df.iloc[len_train:]), ready_full_df[len_train:]]) # Sparse Matrix
tfvocab = full_df.columns.tolist() + tfvocab

for shape in [X,test]:
    print("{} Rows and {} Cols".format(*shape.shape))
print("Feature Names Length: ",len(tfvocab))

cat_col = [
           "user_id",
           "region", 
           "city", 
           "parent_category_name",
           "category_name", 
           "user_type", 
           "image_top_1",
           "param_1", 
           "param_2", 
           "param_3",
           ]
# Begin trainning
X_train, X_valid, y_train, y_valid = train_test_split(
    X, y, test_size=0.1, random_state=42) #23

lgbm_params =  {
        "tree_method": "feature",    
        "num_threads": 6,
        "task": "train",
        "boosting_type": "gbdt",
        "objective": "regression",
        "metric": "rmse",
        "max_depth": 15,
        "num_leaves": 35,
        "feature_fraction": 0.7,
        "bagging_fraction": 0.8,#0.8
        "learning_rate": 0.019,#0.019
        "verbose": -1,
        'lambda_l2':1,
        }

lgtrain = lgb.Dataset(X_train, y_train,
                feature_name=tfvocab,
                categorical_feature = cat_col)
lgvalid = lgb.Dataset(X_valid, y_valid,
                feature_name=tfvocab,
                categorical_feature = cat_col)
lgb_clf = lgb.train(
        lgbm_params,
        lgtrain,
        num_boost_round=32000,
        valid_sets=[lgtrain, lgvalid],
        valid_names=["train","valid"],
        early_stopping_rounds=500,
        verbose_eval=100, #200
        )

print("save model ...")
joblib.dump(lgb_clf, "lgb.pkl")
# load model
#lgb_clf = joblib.load("lgb.pkl")

print("Model Evaluation Stage")
print( "RMSE:", rmse(y_valid, lgb_clf.predict(X_valid, num_iteration=lgb_clf.best_iteration)) )
lgpred = lgb_clf.predict(test, num_iteration=lgb_clf.best_iteration)

lgsub = pd.DataFrame(lgpred,columns=["deal_probability"],index=sub_item_id)
lgsub["deal_probability"].clip(0.0, 1.0, inplace=True) # Between 0 and 1
lgsub.to_csv("ml_lgb_sub.csv",index=True,header=True)

print("Features importance...")
bst = lgb_clf
gain = bst.feature_importance("gain")
ft = pd.DataFrame({"feature":bst.feature_name(), "split":bst.feature_importance("split"), "gain":100 * gain / gain.sum()}).sort_values("gain", ascending=False)
print(ft.head(50))

plt.figure()
ft[["feature","gain"]].head(50).plot(kind="barh", x="feature", y="gain", legend=False, figsize=(10, 20))
plt.gcf().savefig("features_importance.png")

print("Done.")


"""
Training until validation scores don't improve for 500 rounds.
[100]	train's rmse: 0.224061	valid's rmse: 0.224797
[200]	train's rmse: 0.220234	valid's rmse: 0.221972
[300]	train's rmse: 0.218236	valid's rmse: 0.22083
[400]	train's rmse: 0.21684	valid's rmse: 0.220161


Early stopping, best iteration is:
[9425]	train's rmse: 0.196686	valid's rmse: 0.217877

LB: 0.2224
[100]   train's rmse: 0.224567  valid's rmse: 0.225292
[10890] train's rmse: 0.194888  valid's rmse: 0.217884

"""