#encoding=utf-8
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
import time

print("Starting job at time:",time.time())
debug = False
print("loading data ...")
used_cols = ["item_id", "user_id"]
if debug == False:
    train_df = pd.read_csv("input/train.csv",  parse_dates = ["activation_date"])
    y = train_df["deal_probability"]
    test_df = pd.read_csv("input/test.csv",  parse_dates = ["activation_date"])
    # suppl
    train_active = pd.read_csv("input/train_active.csv", usecols=used_cols)
    test_active = pd.read_csv("input/test_active.csv", usecols=used_cols)
    train_periods = pd.read_csv("input/periods_train.csv", parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("input/periods_test.csv", parse_dates=["date_from", "date_to"])
else:
    train_df = pd.read_csv("input/train.csv", parse_dates = ["activation_date"])
    train_df = shuffle(train_df, random_state=1234); train_df = train_df.iloc[:100000]
    y = train_df["deal_probability"]
    test_df = pd.read_csv("input/test.csv",  nrows=1000, parse_dates = ["activation_date"])
    # suppl 
    train_active = pd.read_csv("input/train_active.csv",  nrows=1000, usecols=used_cols)
    test_active = pd.read_csv("input/test_active.csv",  nrows=1000, usecols=used_cols)
    train_periods = pd.read_csv("input/periods_train.csv",  nrows=1000, parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("input/periods_test.csv",  nrows=1000, parse_dates=["date_from", "date_to"])
print("loading data done!")



# =============================================================================
# Add image quality: by steeve
# ============================================================================= 
import pickle
with open('input/inception_v3_include_head_max_train.p','rb') as f:
    x = pickle.load(f)
    
train_features = x['features']
train_ids = x['ids']

with open('input/inception_v3_include_head_max_test.p','rb') as f:
    x = pickle.load(f)

test_features = x['features']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_features, columns = ['image_quality'])
incep_test_image_df = pd.DataFrame(test_features, columns = [f'image_quality'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)

train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')   

   
with open('input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_blurinesses = x['blurinesses']
train_ids = x['ids']

with open('input/test_image_features.p','rb') as f:
    x = pickle.load(f)

test_blurinesses = x['blurinesses']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_blurinesses, columns = ['blurinesses'])
incep_test_image_df = pd.DataFrame(test_blurinesses, columns = [f'blurinesses'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding whitenesses ...')
with open('input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_whitenesses = x['whitenesses']
train_ids = x['ids']


with open('input/test_image_features.p','rb') as f:
    x = pickle.load(f)

test_whitenesses = x['whitenesses']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_whitenesses, columns = ['whitenesses'])
incep_test_image_df = pd.DataFrame(test_whitenesses, columns = [f'whitenesses'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding dullnesses ...')
with open('input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_dullnesses = x['dullnesses']
train_ids = x['ids']

with open('input/test_image_features.p','rb') as f:
    x = pickle.load(f)

test_dullnesses = x['dullnesses']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_dullnesses, columns = ['dullnesses'])
incep_test_image_df = pd.DataFrame(test_dullnesses, columns = [f'dullnesses'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


# =============================================================================
# new image data
# =============================================================================

print('adding average_pixel_width ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_pixel_width = x['average_pixel_width']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_average_pixel_width = x['average_pixel_width']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_average_pixel_width, columns = ['average_pixel_width'])
incep_test_image_df = pd.DataFrame(test_average_pixel_width, columns = [f'average_pixel_width'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding average_reds ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_reds = x['average_reds']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_average_reds = x['average_reds']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_average_reds, columns = ['average_reds'])
incep_test_image_df = pd.DataFrame(test_average_reds, columns = [f'average_reds'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding average_blues ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_blues = x['average_blues']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_average_blues = x['average_blues']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_average_blues, columns = ['average_blues'])
incep_test_image_df = pd.DataFrame(test_average_blues, columns = [f'average_blues'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding average_greens ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_greens = x['average_greens']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_average_greens = x['average_greens']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_average_greens, columns = ['average_greens'])
incep_test_image_df = pd.DataFrame(test_average_greens, columns = [f'average_greens'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding widths ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_widths = x['widths']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_widths = x['widths']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_widths, columns = ['widths'])
incep_test_image_df = pd.DataFrame(test_widths, columns = [f'widths'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')


print('adding heights ...')
with open('input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_heights = x['heights']
train_ids = x['ids']

with open('input/test_image_features_1.p','rb') as f:
    x = pickle.load(f)

test_heights = x['heights']
test_ids = x['ids']    
del x; gc.collect()


incep_train_image_df = pd.DataFrame(train_heights, columns = ['heights'])
incep_test_image_df = pd.DataFrame(test_heights, columns = [f'heights'])
incep_train_image_df['image'] = (train_ids)
incep_test_image_df['image'] = (test_ids)
train_df = train_df.join(incep_train_image_df.set_index('image'), on='image')
test_df = test_df.join(incep_test_image_df.set_index('image'), on='image')

#==============================================================================
# image features by Qifeng
#==============================================================================
print('adding image features ...')
with open('input/train_image_features_cspace.p','rb') as f:
    x = pickle.load(f)

x_train = pd.DataFrame(x, columns = ['average_HSV_Ss',\
                                     'average_HSV_Vs',\
                                     'average_LUV_Ls',\
                                     'average_LUV_Us',\
                                     'average_LUV_Vs',\
                                     'average_HLS_Hs',\
                                     'average_HLS_Ls',\
                                     'average_HLS_Ss',\
                                     'average_YUV_Ys',\
                                     'average_YUV_Us',\
                                     'average_YUV_Vs',\
                                     'ids'
                                     ])
#x_train.rename(columns = {'$ids':'image'}, inplace = True)

with open('input/test_image_features_cspace.p','rb') as f:
    x = pickle.load(f)

x_test = pd.DataFrame(x, columns = ['average_HSV_Ss',\
                                     'average_HSV_Vs',\
                                     'average_LUV_Ls',\
                                     'average_LUV_Us',\
                                     'average_LUV_Vs',\
                                     'average_HLS_Hs',\
                                     'average_HLS_Ls',\
                                     'average_HLS_Ss',\
                                     'average_YUV_Ys',\
                                     'average_YUV_Us',\
                                     'average_YUV_Vs',\
                                     'ids'
                                    ])
#x_test.rename(columns = {'$ids':'image'}, inplace = True)

train_df = train_df.join(x_train.set_index('ids'), on='image')
test_df = test_df.join(x_test.set_index('ids'), on='image')
del x, x_train, x_test; gc.collect()
# =============================================================================
# add geo info: https://www.kaggle.com/frankherfert/avito-russian-region-cities/data
# =============================================================================
#tmp = pd.read_csv("../input/avito_region_city_features.csv", usecols=["region", "city", "latitude","longitude"])
#train_df = train_df.merge(tmp, on=["city","region"], how="left")
#train_df["lat_long"] = train_df["latitude"]+train_df["longitude"]
#test_df = test_df.merge(tmp, on=["city","region"], how="left")
#test_df["lat_long"] = test_df["latitude"]+test_df["longitude"]
#del tmp; gc.collect()

# =============================================================================
# Add region-income
# =============================================================================
tmp = pd.read_csv("input/region_income.csv", sep=";", names=["region", "income"])
train_df = train_df.merge(tmp, on="region", how="left")
test_df = test_df.merge(tmp, on="region", how="left")
del tmp; gc.collect()
# =============================================================================
# Add region-income
# =============================================================================
tmp = pd.read_csv("input/city_population_wiki_v3.csv")
train_df = train_df.merge(tmp, on="city", how="left")
test_df = test_df.merge(tmp, on="city", how="left")
del tmp; gc.collect()

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
gp = gp.merge(n_user_items, on="user_id", how="outer") #left

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

def text_preprocessing(text):        
    text = str(text)
    text = text.lower()
    text = re.sub(r"(\\u[0-9A-Fa-f]+)",r"", text)    
    text = re.sub(r"===",r" ", text)   
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
        df["text_feature"] = df["text_feature"].apply(lambda x: text_preprocessing(x))
        df["text_feature_2"] = df["text_feature_2"].apply(lambda x: text_preprocessing(x))
        df["description"] = df["description"].apply(lambda x: text_preprocessing(x))
        df["title"] = df["title"].apply(lambda x: text_preprocessing(x))
        df["title_description"] = df["title_description"].apply(lambda x: text_preprocessing(x))
                       
    def Do_Datetime(df):
        print("feature engineering -> date time ...")
        df["wday"] = df["activation_date"].dt.weekday
        df["wday"] =df["wday"].astype(np.uint8)
        
    def Do_Label_Enc(df):
        print("feature engineering -> lable encoding ...")
        lbl = LabelEncoder()
        cat_col = ["user_id", "region", "city", "parent_category_name",
               "category_name", "user_type", "image_top_1",
               "param_1", "param_2", "param_3","image",
               ]
        for col in cat_col:
            df[col] = lbl.fit_transform(df[col].astype(str))
            gc.collect()
    
    import string
    count = lambda l1,l2: sum([1 for x in l1 if x in l2])         
    def Do_NA(df):
        print("feature engineering -> fill na ...")
                
        df["image_top_1"].fillna(-1,inplace=True)
        df["image"].fillna("noinformation",inplace=True)
        df["param_1"].fillna("nicapotato",inplace=True)
        df["param_2"].fillna("nicapotato",inplace=True)
        df["param_3"].fillna("nicapotato",inplace=True)
        df["title"].fillna("nicapotato",inplace=True)
        df["description"].fillna("nicapotato",inplace=True)
        # price vs income
#        df["price_vs_city_income"] = df["price"] / df["income"]
#        df["price_vs_city_income"].fillna(-1, inplace=True)
        df['average_HSV_Ss'].fillna(-1,inplace=True)
        df['average_HSV_Vs'].fillna(-1,inplace=True)
        df['average_LUV_Ls'].fillna(-1,inplace=True)
        df['average_LUV_Us'].fillna(-1,inplace=True)
        df['average_LUV_Vs'].fillna(-1,inplace=True)
        df['average_HLS_Hs'].fillna(-1,inplace=True)
        df['average_HLS_Ls'].fillna(-1,inplace=True)
        df['average_HLS_Ss'].fillna(-1,inplace=True)
        df['average_YUV_Ys'].fillna(-1,inplace=True)
        df['average_YUV_Us'].fillna(-1,inplace=True)
        df['average_YUV_Vs'].fillna(-1,inplace=True)
        
        
    def Do_Count(df):  
        print("feature engineering -> do count ...")
        # some count       
        df["num_desc_punct"] = df["description"].apply(lambda x: count(x, set(string.punctuation))).astype(np.int16)
        df["num_desc_capE"] = df["description"].apply(lambda x: count(x, "[A-Z]")).astype(np.int16)
        df["num_desc_capP"] = df["description"].apply(lambda x: count(x, "[А-Я]")).astype(np.int16)
        
        df["num_title_punct"] = df["title"].apply(lambda x: count(x, set(string.punctuation))).astype(np.int16)
        df["num_title_capE"] = df["title"].apply(lambda x: count(x, "[A-Z]")).astype(np.int16)
        df["num_title_capP"] = df["title"].apply(lambda x: count(x, "[А-Я]"))  .astype(np.int16)
        # good, used, bad ... count
        df["is_in_desc_хорошо"] = df["description"].str.contains("хорошо").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_Плохо"] = df["description"].str.contains("Плохо").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_новый"] = df["description"].str.contains("новый").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_старый"] = df["description"].str.contains("старый").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_используемый"] = df["description"].str.contains("используемый").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_есплатная_доставка"] = df["description"].str.contains("есплатная доставка").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_есплатный_возврат"] = df["description"].str.contains("есплатный возврат").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_идеально"] = df["description"].str.contains("идеально").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_подержанный"] = df["description"].str.contains("подержанный").map({True:1, False:0}).astype(np.uint8)
        df["is_in_desc_пСниженные_цены"] = df["description"].str.contains("Сниженные цены").map({True:1, False:0}).astype(np.uint8)
        
        # new count 0604
        df["num_title_Exclamation"] = df["title"].apply(lambda x: count(x, "!")).astype(np.int16)
        df["num_title_Question"] = df["title"].apply(lambda x: count(x, "?")).astype(np.int16)
         
        df["num_desc_Exclamation"] = df["description"].apply(lambda x: count(x, "!")).astype(np.int16)
        df["num_desc_Question"] = df["description"].apply(lambda x: count(x, "?")).astype(np.int16)        
                              
    def Do_Drop(df):
        df.drop(["activation_date", "item_id"], axis=1, inplace=True)
        
    def Do_Stat_Text(df):
        print("feature engineering -> statistics in text ...")
        textfeats = ["text_feature","text_feature_2","description", "title"]
        for col in textfeats:
            df[col + "_num_chars"] = df[col].apply(len).astype(np.int16)
            df[col + "_num_words"] = df[col].apply(lambda comment: len(comment.split())).astype(np.int16)
            df[col + "_num_unique_words"] = df[col].apply(lambda comment: len(set(w for w in comment.split()))).astype(np.int16)
            df[col + "_words_vs_unique"] = (df[col+"_num_unique_words"] / df[col+"_num_words"] * 100).astype(np.float32)
            gc.collect()
                      
    # choose which functions to run
    Do_NA(df)
    Do_Text_Hash(df)
    Do_Label_Enc(df)
    Do_Count(df)
    Do_Datetime(df)   
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

    tfidf_para2 = {
        "stop_words": russian_stop,
        "analyzer": "char",
        "token_pattern": r"\w{1,}",
        "sublinear_tf": True,
        "dtype": np.float32,
        "norm": "l2",
        # "min_df":5,
        # "max_df":.9,
        "smooth_idf": False
    }

    def get_col(col_name): return lambda x: x[col_name]
    vectorizer = FeatureUnion([
        ("description", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=40000,#40000,18000
            **tfidf_para,
            preprocessor=get_col("description"))
         ),
#         ("title_description", TfidfVectorizer(
#              ngram_range=(1, 2),#(1,2)
#              max_features=1800,#40000,18000
#              **tfidf_para,
#              preprocessor=get_col("title_description"))
#           ), 
        ("text_feature", CountVectorizer(
            ngram_range=(1, 2),
            preprocessor=get_col("text_feature"))
         ),
      
        ("title", TfidfVectorizer(
            ngram_range=(1, 2),
            **tfidf_para,
            preprocessor=get_col("title"))
         ),
        #新加入两个文本处理title2，title_char
        ("title2", TfidfVectorizer(
            ngram_range=(1, 1),
            **tfidf_para,
            preprocessor=get_col("title"))
         ),

#        ("title_char", TfidfVectorizer(
#
#            ngram_range=(1, 4),#(1, 4),(1,6)
#            max_features=16000,#16000
#            **tfidf_para2,
#            preprocessor=get_col("title"))
#         ),
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
#        print('Ridege oof Fold {}'.format(i))
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
# =============================================================================
# handle price
# =============================================================================
def feature_Eng_On_Price_SEQ(df):
    print('feature engineering -> on price and SEQ ...')
    df["price"] = np.log(df["price"]+0.001).astype("float32")
    df["price"].fillna(-1,inplace=True) 
    df["price+"] = np.round(df["price"]*2.8).astype(np.int16) # 4.8
    df["item_seq_number+"] = np.round(df["item_seq_number"]/100).astype(np.int16)
    return df


train_df, val_df = train_test_split(
    full_df.iloc[:len_train], test_size=0.1, random_state=42) #23
  
def feature_Eng_On_Deal_Prob(df, df_train):
    print('feature engineering -> on price deal prob +...')
    df2 = df    
#    tmp = df_train.groupby(["price+"], as_index=False)['deal_probability'].median().rename(columns={'deal_probability':'median_deal_probability_price+'})     
#    df = pd.merge(df, tmp, how='left', on=["price+"])
#    df2['median_deal_probability_price+'] = df['median_deal_probability_price+']
#    df2['median_deal_probability_price+'] =df2['median_deal_probability_price+'].astype(np.float32)
#    del tmp; gc.collect()
#    
#    tmp = df_train.groupby(["item_seq_number+"], as_index=False)['deal_probability'].median().rename(columns={'deal_probability':'median_deal_probability_item_seq_number+'})     
#    df = pd.merge(df, tmp, how='left', on=["item_seq_number+"])
#    df2['median_deal_probability_item_seq_number+'] = df['median_deal_probability_item_seq_number+']
#    df2['median_deal_probability_item_seq_number+'] =df2['median_deal_probability_item_seq_number+'].astype(np.float32)


#    tmp = df.groupby(["image_top_1"], as_index=False)['price'].median().rename(columns={'price':'median_price_image_top_1'})     
#    df = pd.merge(df, tmp, how='left', on=["image_top_1"])
#    df2['median_price_image_top_1'] = df['median_price_image_top_1']
#    df2['median_price_image_top_1'] = df2['median_price_image_top_1'].astype(np.float32)
#    df2['median_price_image_top_1'] = df2['median_price_image_top_1']
#    df2.fillna(-1, inplace=True)    
    
#    del tmp; gc.collect()
    
    return df2

del full_df['deal_probability']; gc.collect()

# =============================================================================
# use additianl image data
# =============================================================================
feature_engineering(full_df)

feature_Eng_On_Price_SEQ(full_df)
#feature_Eng_On_Price_SEQ(train_df)
# 不考虑使用均值
#feature_Eng_On_Deal_Prob(full_df, train_df)

del train_df, test_df; gc.collect()
full_df, ready_full_df, tfvocab = data_vectorize(full_df)

#'alpha':20.0
ridge_params = {'alpha':20.0, 'fit_intercept':True, 'normalize':False, 'copy_X':True,
                'max_iter':None, 'tol':0.001, 'solver':'auto', 'random_state':SEED}
ridge = SklearnWrapper(clf=Ridge, seed = SEED, params = ridge_params)
ready_df = ready_full_df

print('ridge 1 oof ...')
ridge_oof_train, ridge_oof_test = get_oof(ridge, np.array(full_df)[:len_train], y, np.array(full_df)[len_train:])
ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
full_df['ridge_preds_1'] = ridge_preds
full_df['ridge_preds_1'].clip(0.0, 1.0, inplace=True)

print('ridge 2 oof ...')
ridge_oof_train, ridge_oof_test = get_oof(ridge, ready_df[:len_train], y, ready_df[len_train:])
ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
full_df['ridge_preds_2'] = ridge_preds
full_df['ridge_preds_2'].clip(0.0, 1.0, inplace=True)

del ridge_oof_train, ridge_oof_test, ridge_preds,ridge, ready_df
gc.collect()

# 内存优化
full_df["average_blues"] = full_df["average_blues"].astype(np.float32)
full_df["average_greens"] = full_df["average_greens"].astype(np.float32)
full_df["average_pixel_width"] = full_df["average_pixel_width"].astype(np.float32)
full_df["average_reds"] = full_df["average_reds"].astype(np.float32)
full_df["avg_days_up_user"] = full_df["avg_days_up_user"].astype(np.float32)
full_df["avg_times_up_user"] = full_df["avg_times_up_user"].astype(np.float32)
full_df["blurinesses"] = full_df["blurinesses"].astype(np.float32)
full_df["dullnesses"] = full_df["dullnesses"].astype(np.float32)
full_df["heights"] = full_df["heights"].astype(np.float32)
full_df["parent_category_name"] = full_df["parent_category_name"].astype(np.float32)
full_df["whitenesses"] = full_df["whitenesses"].astype(np.float32)
full_df["widths"] = full_df["widths"].astype(np.float32)
full_df["ridge_preds_1"] = full_df["ridge_preds_1"].astype(np.float32)
full_df["ridge_preds_2"] = full_df["ridge_preds_2"].astype(np.float32)
full_df["category_name"] = full_df["category_name"].astype(np.int32)
full_df["city"] = full_df["city"].astype(np.int32)
full_df["image"] = full_df["image"].astype(np.int32)
full_df["image_top_1"] = full_df["image_top_1"].astype(np.int32)
full_df["income"] = full_df["income"].astype(np.int32)
full_df["item_seq_number"] = full_df["item_seq_number"].astype(np.int32)
full_df["n_user_items"] = full_df["n_user_items"].astype(np.int32)
full_df["param_1"] = full_df["param_1"].astype(np.int32)
full_df["param_2"] = full_df["param_2"].astype(np.int32)
full_df["param_3"] = full_df["param_3"].astype(np.int32)
full_df["parent_category_name"] = full_df["parent_category_name"].astype(np.int32)
full_df["region"] = full_df["region"].astype(np.int32)
full_df["user_id"] = full_df["user_id"].astype(np.int32)
full_df["user_type"] = full_df["user_type"].astype(np.int32)
full_df["population"] = full_df["population"].astype(np.int32)
gc.collect()
# mean rmse is: 0.23904413087329351

print("Modeling Stage ...")
# Combine Dense Features with Sparse Text Bag of Words Features
X = hstack([csr_matrix(full_df.iloc[:len_train]), ready_full_df[:len_train]]) # Sparse Matrix
tfvocab = full_df.columns.tolist() + tfvocab
X_test_full=full_df.iloc[len_train:]
X_test_ready=ready_full_df[len_train:]
del ready_full_df,full_df
gc.collect()



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
           "price+",
           "item_seq_number+",
           ]

from sklearn.model_selection import KFold

kf = KFold(n_splits=10, random_state=42, shuffle=True)
numIter = 0
rmse_sume = 0.
numLimit = 2

for train_index, valid_index in kf.split(y):
      numIter +=1
      print("training in fold " + str(numIter))
      
      if numIter>=numLimit+1:
            pass
      else:
      
            print("Modeling Stage ...")    
            
            X_train, X_valid = X.tocsr()[train_index], X.tocsr()[valid_index]
            y_train, y_valid = y.iloc[train_index], y.iloc[valid_index]
            
            gc.collect()
            
            lgbm_params =  {
#                    "gpu_platform_id":-1,
#                    "gpu_device_id":-1,
                    "tree_learner": "feature",    
                    "num_threads": 3,
                    "task": "train",
                    "boosting_type": "gbdt",
                    "objective": "regression",
                    "metric": "rmse",
                   # "max_depth": 15,
                    "num_leaves": 500, # 500, 280,360,500,32
                    "feature_fraction": 0.2, #0.4
                    "bagging_fraction": 0.2, #0.4
                    "learning_rate": 0.015,#0.015
                    "verbose": -1,
                    'lambda_l1':1,
                    'lambda_l2':1,
                    "max_bin":200,
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
                    early_stopping_rounds=200,
                    verbose_eval=100, #200
                    )
            
            print("save model ...")
            joblib.dump(lgb_clf, "lgb_{}.pkl".format(numIter))
            ## load model
            #lgb_clf = joblib.load("lgb.pkl")
            
            print("Model Evaluation Stage")
            print( "RMSE:", rmse(y_valid, lgb_clf.predict(X_valid, num_iteration=lgb_clf.best_iteration)) )
      
            test = hstack([csr_matrix(X_test_full), X_test_ready])  # Sparse Matrix
            lgpred = lgb_clf.predict(test, num_iteration=lgb_clf.best_iteration)
            
            lgsub = pd.DataFrame(lgpred,columns=["deal_probability"],index=sub_item_id)
            lgsub["deal_probability"].clip(0.0, 1.0, inplace=True) # Between 0 and 1
            lgsub.to_csv("ml_lgb_sub_{}.csv".format(numIter),index=True,header=True)
      
            rmse_sume += rmse(y_valid, lgb_clf.predict(X_valid, num_iteration=lgb_clf.best_iteration))
                  
            del X_train, X_valid, y_train, y_valid, lgtrain, lgvalid
            gc.collect()
      

print("mean rmse is:", rmse_sume/numLimit)
      
print("Features importance...")
bst = lgb_clf
gain = bst.feature_importance("gain")
ft = pd.DataFrame({"feature":bst.feature_name(), "split":bst.feature_importance("split"), "gain":100 * gain / gain.sum()}).sort_values("gain", ascending=False)
print(ft.head(50))
#
#plt.figure()
#ft[["feature","gain"]].head(50).plot(kind="barh", x="feature", y="gain", legend=False, figsize=(10, 20))
#plt.gcf().savefig("features_importance.png")

print("All Done.")


"""
[100]   train's rmse: 0.225334  valid's rmse: 0.227747
[200]   train's rmse: 0.216325  valid's rmse: 0.221314
[300]   train's rmse: 0.211557  valid's rmse: 0.219024
[400]   train's rmse: 0.207684  valid's rmse: 0.217669
[500]   train's rmse: 0.20463   valid's rmse: 0.216868
[600]   train's rmse: 0.202079  valid's rmse: 0.216283
[700]   train's rmse: 0.199632  valid's rmse: 0.215872
[800]   train's rmse: 0.197357  valid's rmse: 0.215542
[900]   train's rmse: 0.195246  valid's rmse: 0.215284
[1000]  train's rmse: 0.193335  valid's rmse: 0.215103
[1100]  train's rmse: 0.191585  valid's rmse: 0.214956
[1200]  train's rmse: 0.189951  valid's rmse: 0.214829
[1300]  train's rmse: 0.188327  valid's rmse: 0.214733
[1400]  train's rmse: 0.186788  valid's rmse: 0.214657
[1500]  train's rmse: 0.185445  valid's rmse: 0.214618
[1600]  train's rmse: 0.184096  valid's rmse: 0.214571
[1700]  train's rmse: 0.182753  valid's rmse: 0.214529
[1800]  train's rmse: 0.181524  valid's rmse: 0.214492
[1900]  train's rmse: 0.180362  valid's rmse: 0.214467
[2000]  train's rmse: 0.179283  valid's rmse: 0.214453
[2100]  train's rmse: 0.178173  valid's rmse: 0.214428
[2200]  train's rmse: 0.177125  valid's rmse: 0.214419
[2300]  train's rmse: 0.176059  valid's rmse: 0.214398
[2400]  train's rmse: 0.175013  valid's rmse: 0.214373
[2500]  train's rmse: 0.174059  valid's rmse: 0.21436
[2600]  train's rmse: 0.173117  valid's rmse: 0.214342
[2700]  train's rmse: 0.17219   valid's rmse: 0.214333
[2800]  train's rmse: 0.171297  valid's rmse: 0.214314
[2900]  train's rmse: 0.170378  valid's rmse: 0.214308
[3000]  train's rmse: 0.169473  valid's rmse: 0.214296
[3100]  train's rmse: 0.168633  valid's rmse: 0.214289
[3200]  train's rmse: 0.16778   valid's rmse: 0.214289
[3300]  train's rmse: 0.16696   valid's rmse: 0.214289
[3400]  train's rmse: 0.16611   valid's rmse: 0.214284
[3500]  train's rmse: 0.165331  valid's rmse: 0.214282
[3600]  train's rmse: 0.164559  valid's rmse: 0.214283
[3700]  train's rmse: 0.163756  valid's rmse: 0.214282
Early stopping, best iteration is:
[3552]  train's rmse: 0.164908  valid's rmse: 0.21428
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.21427999456912336
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
training in fold 2
Modeling Stage ...
Training until validation scores don't improve for 200 rounds.
[100]   train's rmse: 0.224902  valid's rmse: 0.226517
[200]   train's rmse: 0.216455  valid's rmse: 0.220604
[300]   train's rmse: 0.212004  valid's rmse: 0.218416
[400]   train's rmse: 0.208483  valid's rmse: 0.217155
[500]   train's rmse: 0.2055    valid's rmse: 0.216319
[600]   train's rmse: 0.20293   valid's rmse: 0.215782
[700]   train's rmse: 0.200601  valid's rmse: 0.215321
[800]   train's rmse: 0.198348  valid's rmse: 0.214937
[900]   train's rmse: 0.196329  valid's rmse: 0.21469
[1000]  train's rmse: 0.194463  valid's rmse: 0.214516
[1100]  train's rmse: 0.192611  valid's rmse: 0.214353
[1200]  train's rmse: 0.190888  valid's rmse: 0.214205
[1300]  train's rmse: 0.189285  valid's rmse: 0.214116
[1400]  train's rmse: 0.187753  valid's rmse: 0.21404
[1500]  train's rmse: 0.186332  valid's rmse: 0.213974
[1600]  train's rmse: 0.184889  valid's rmse: 0.213914
[1700]  train's rmse: 0.183542  valid's rmse: 0.21388
[1800]  train's rmse: 0.182302  valid's rmse: 0.213839
[1900]  train's rmse: 0.181063  valid's rmse: 0.213806
[2000]  train's rmse: 0.179857  valid's rmse: 0.213777
[2100]  train's rmse: 0.17867   valid's rmse: 0.213746
[2200]  train's rmse: 0.177503  valid's rmse: 0.213729
[2300]  train's rmse: 0.176495  valid's rmse: 0.213699
[2400]  train's rmse: 0.175565  valid's rmse: 0.213686
[2500]  train's rmse: 0.174568  valid's rmse: 0.213664
[2600]  train's rmse: 0.173584  valid's rmse: 0.213665
Early stopping, best iteration is:
[2498]  train's rmse: 0.174583  valid's rmse: 0.213664
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.21366355168192042
calculating RMSE ...
training in fold 3
training in fold 4
training in fold 5
training in fold 6
training in fold 7
training in fold 8
training in fold 9
training in fold 10
mean rmse is: 0.2139717731255219
Features importance...
                               feature       gain  split
79                       ridge_preds_2  12.261748  15862
24                         image_top_1  10.842806  77328
28                             param_1   6.584938  27880
18                       category_name   5.654216  14824
19                                city   5.028092  57581
29                             param_2   3.429071  15085
78                       ridge_preds_1   2.506257  13760
33                               price   2.095278  15963
30                             param_3   1.851032  14865
27                        n_user_items   1.792695  10681
76                              price+   1.692630  13797
31                parent_category_name   1.604904   3396
34                              region   1.590102  30201
35                             user_id   1.080422  10808
15                    avg_days_up_user   1.050378  12607
16                   avg_times_up_user   0.698825   8277
26                     item_seq_number   0.686239  12993
32                          population   0.620647  12391
66     text_feature_2_num_unique_words   0.592943   1082
6                       average_LUV_Us   0.559214  11460
77                    item_seq_number+   0.440776   4944
68               description_num_chars   0.436932  10067
8                       average_YUV_Us   0.409056   9989
4                       average_HSV_Vs   0.399653  10661
17                         blurinesses   0.394840  11138
9                       average_YUV_Vs   0.394201  10901
69               description_num_words   0.383455   7841
3                       average_HSV_Ss   0.374136  11119
13                 average_pixel_width   0.364044  11952
60              text_feature_num_chars   0.357137   4785
11                       average_blues   0.345213   9892
39                      num_desc_punct   0.344902   6877
7                       average_LUV_Vs   0.344089  10189
10                      average_YUV_Ys   0.339887   9325
5                       average_LUV_Ls   0.336960   8838
14                        average_reds   0.336850   9974
1                       average_HLS_Ls   0.333027   7880
0                       average_HLS_Hs   0.331031  10646
2                       average_HLS_Ss   0.329830  11011
36                           user_type   0.323575   1829
23                       image_quality   0.318838  11340
33350           description__состоянии   0.304941   4195
72                     title_num_chars   0.304474   8545
12                      average_greens   0.298981   9085
70        description_num_unique_words   0.293297   7457
38                              widths   0.285472   5572
41587         text_feature__nicapotato   0.283500    765
22                               image   0.278822  11095
63        text_feature_words_vs_unique   0.236211   1761
62       text_feature_num_unique_words   0.225217   1977
All Done.

runfile('/home/qifeng/avito/ensemble_corr.py', wdir='/home/qifeng/avito')
correlation between models outputs
          dp1       dp2
dp1  1.000000  0.986174
dp2  0.986174  1.000000

"""
