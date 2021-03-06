#encoding=utf-8
from nltk.corpus import stopwords
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import Ridge
from scipy.sparse import hstack, csr_matrix
import pandas as pd
import numpy as np
import lightgbm as lgb
#import matplotlib.pyplot as plt
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
    train_df = pd.read_csv("../input/train.csv",  parse_dates = ["activation_date"])
    y = train_df["deal_probability"]
    test_df = pd.read_csv("../input/test.csv",  parse_dates = ["activation_date"])

    train_active = pd.read_csv("../input/train_active.csv", usecols=used_cols)
    test_active = pd.read_csv("../input/test_active.csv", usecols=used_cols)
    train_periods = pd.read_csv("../input/periods_train.csv", parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("../input/periods_test.csv", parse_dates=["date_from", "date_to"])
else:
    train_df = pd.read_csv("../input/train.csv", parse_dates = ["activation_date"])
    train_df = shuffle(train_df, random_state=1234); train_df = train_df.iloc[:10000]
    y = train_df["deal_probability"]
    test_df = pd.read_csv("../input/test.csv",  nrows=1000, parse_dates = ["activation_date"])
    
    train_active = pd.read_csv("../input/train_active.csv",  nrows=10000, usecols=used_cols)
    test_active = pd.read_csv("../input/test_active.csv",  nrows=10000, usecols=used_cols)
    train_periods = pd.read_csv("../input/periods_train.csv",  nrows=10000, parse_dates=["date_from", "date_to"])
    test_periods = pd.read_csv("../input/periods_test.csv",  nrows=10000, parse_dates=["date_from", "date_to"])
print("loading data done!")


# =============================================================================
# Add image quality: by steeve
# ============================================================================= 
import pickle
with open('../input/inception_v3_include_head_max_train.p','rb') as f:
    x = pickle.load(f)
    
train_features = x['features']
train_ids = x['ids']

with open('../input/inception_v3_include_head_max_test.p','rb') as f:
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

del incep_train_image_df, incep_test_image_df
gc.collect()

 
with open('../input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_blurinesses = x['blurinesses']
train_ids = x['ids']

with open('../input/test_image_features.p','rb') as f:
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
with open('../input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_whitenesses = x['whitenesses']
train_ids = x['ids']


with open('../input/test_image_features.p','rb') as f:
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
with open('../input/train_image_features.p','rb') as f:
    x = pickle.load(f)
    
train_dullnesses = x['dullnesses']
train_ids = x['ids']

with open('../input/test_image_features.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_pixel_width = x['average_pixel_width']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_reds = x['average_reds']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_blues = x['average_blues']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_average_greens = x['average_greens']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_widths = x['widths']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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
with open('../input/train_image_features_1.p','rb') as f:
    x = pickle.load(f)
    
train_heights = x['heights']
train_ids = x['ids']

with open('../input/test_image_features_1.p','rb') as f:
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


del test_average_blues, test_average_greens, test_average_reds, incep_test_image_df
del train_average_blues, train_average_greens, train_average_reds, incep_train_image_df
gc.collect()


#==============================================================================
# image features by Qifeng
#==============================================================================
print('adding image features @ qifeng ...')
with open('../input/train_image_features_cspace.p','rb') as f:
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

with open('../input/test_image_features_cspace.p','rb') as f:
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
tmp = pd.read_csv("../input/region_income.csv", sep=";", names=["region", "income"])
train_df = train_df.merge(tmp, on="region", how="left")
test_df = test_df.merge(tmp, on="region", how="left")
del tmp; gc.collect()
# =============================================================================
# Add region-income
# =============================================================================
tmp = pd.read_csv("../input/city_population_wiki_v3.csv")
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
# impute https://www.kaggle.com/krithi07/baseline-model-with-new-features 0.227456
# =============================================================================
# New variables #
#print("https://www.kaggle.com/krithi07/baseline-model-with-new-features")
train_prd = pd.read_csv("../input/periods_train.csv", parse_dates=["activation_date","date_from", "date_to"])
test_prd = pd.read_csv("../input/periods_test.csv", parse_dates=["activation_date","date_from", "date_to"])
print("Period Train file rows and columns are : ", train_prd.shape)
print("Period Test file rows and columns are : ", test_prd.shape)
#Number of days an ad was active on the portal
train_prd['days'] = (train_prd['date_to'] - train_prd['date_from']).dt.days
test_prd['days'] = (test_prd['date_to'] - test_prd['date_from']).dt.days

enc = train_prd.groupby('item_id')['days'].agg('sum').astype(np.float32).reset_index()
enc.head(5)

train_df = pd.merge(train_df, enc, how='left', on='item_id')
test_df = pd.merge(test_df, enc, how='left', on='item_id')
del train_prd, test_prd; gc.collect()


#Impute image_top_1
enc = train_df.groupby('category_name')['image_top_1'].agg(lambda x:x.value_counts().index[0]).astype(np.float32).reset_index()
enc.columns = ['category_name' ,'image_top_1_impute']
#Cross Check values
#enc = train_df.loc[train_df['category_name'] == 'Аквариум'].groupby('image_top_1').agg('count')
#enc.sort_values(['item_id'], ascending=False).head(2)

train_df = pd.merge(train_df, enc, how='left', on='category_name')
test_df = pd.merge(test_df, enc, how='left', on='category_name')

train_df['image_top_1'].fillna(train_df['image_top_1_impute'], inplace=True)
test_df['image_top_1'].fillna(test_df['image_top_1_impute'], inplace=True)

#Impute Days diff
enc = train_df.groupby('category_name')['days'].agg('median').astype(np.float32).reset_index()
enc.columns = ['category_name' ,'days_impute']
#Cross Check values
#enc = train_df.loc[train_df['category_name'] == 'Аквариум'].groupby('image_top_1').agg('count')
#enc.sort_values(['item_id'], ascending=False).head(2)

train_df = pd.merge(train_df, enc, how='left', on='category_name')
test_df = pd.merge(test_df, enc, how='left', on='category_name')

train_df['days'].fillna(train_df['days_impute'], inplace=True)
test_df['days'].fillna(test_df['days_impute'], inplace=True)

# City names are duplicated across region, HT: Branden Murray 
#https://www.kaggle.com/c/avito-demand-prediction/discussion/55630#321751
train_df['city'] = train_df['city'] + "_" + train_df['region']
test_df['city'] = test_df['city'] + "_" + test_df['region']

cat_cols = ['category_name', 'image_top_1']
num_cols = ['price', 'deal_probability']

for c in cat_cols:
    for c2 in num_cols:
        enc = train_df.groupby(c)[c2].agg(['median']).astype(np.float32).reset_index()
        enc.columns = ['_'.join([str(c), str(c2), str(c3)]) if c3 != c else c for c3 in enc.columns]
        train_df = pd.merge(train_df, enc, how='left', on=c)
        test_df = pd.merge(test_df, enc, how='left', on=c)



## =============================================================================
## svd on tfid data https://www.kaggle.com/krithi07/baseline-model-with-new-features
## =============================================================================
#### TFIDF Vectorizer ###
#from sklearn.decomposition import TruncatedSVD
#tfidf_vec = TfidfVectorizer(ngram_range=(1,1))
#full_tfidf = tfidf_vec.fit_transform(train_df['title'].values.tolist() + test_df['title'].values.tolist())
#
#train_tfidf = tfidf_vec.transform(train_df['title'].values.tolist())
#test_tfidf = tfidf_vec.transform(test_df['title'].values.tolist())
#
#### SVD Components ###
#n_comp = 5
#svd_obj = TruncatedSVD(n_components=n_comp, algorithm='arpack')
#svd_obj.fit(full_tfidf)
#train_svd = pd.DataFrame(svd_obj.transform(train_tfidf))
#test_svd = pd.DataFrame(svd_obj.transform(test_tfidf))
#train_svd.columns = ['svd_title_'+str(i+1) for i in range(n_comp)]
#test_svd.columns = ['svd_title_'+str(i+1) for i in range(n_comp)]
#train_df = pd.concat([train_df, train_svd], axis=1)
#test_df = pd.concat([test_df, test_svd], axis=1)
#del full_tfidf, train_tfidf, test_tfidf, train_svd, test_svd
#
#train_df['description'].fillna('nicapotato', inplace=True)
#test_df['description'].fillna('nicapotato', inplace=True)
#
#tfidf_vec = TfidfVectorizer(ngram_range=(1,1), max_features=100000)
#full_tfidf = tfidf_vec.fit_transform(train_df['description'].values.tolist() + test_df['description'].values.tolist())
#train_tfidf = tfidf_vec.transform(train_df['description'].values.tolist())
#test_tfidf = tfidf_vec.transform(test_df['description'].values.tolist())
#
#### SVD Components ###
#n_comp = 5
#svd_obj = TruncatedSVD(n_components=n_comp, algorithm='arpack')
#svd_obj.fit(full_tfidf)
#train_svd = pd.DataFrame(svd_obj.transform(train_tfidf))
#test_svd = pd.DataFrame(svd_obj.transform(test_tfidf))
#train_svd.columns = ['svd_desc_'+str(i+1) for i in range(n_comp)]
#test_svd.columns = ['svd_desc_'+str(i+1) for i in range(n_comp)]
#train_df = pd.concat([train_df, train_svd], axis=1)
#test_df = pd.concat([test_df, test_svd], axis=1)
#del full_tfidf, train_tfidf, test_tfidf, train_svd, test_svd




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
        print("feature engineering -> label encoding ...")
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

        # new features
        df["is_in_desc_iphone"] = df["title"].str.contains("iphone").map({True: 1, False: 0}).astype(np.uint8)
        df["is_in_desc_ipod"] = df["title"].str.contains("ipod").map({True: 1, False: 0}).astype(np.uint8)

        df["is_in_desc_samsung"] = df["title"].str.contains("samsung").map({True: 1, False: 0}).astype(np.uint8)

    def Do_Drop(df):
        df.drop(["activation_date"], axis=1, inplace=True)
        
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

# mean rmse is: 0.23865288181138436
    def char_analyzer(text):
        """
        This is used to split strings in small lots
        anttip saw this in an article
        so <talk> and <talking> would have <Tal> <alk> in common
        should be similar to russian I guess
        """
        tokens = text.split()
        return [token[i: i + 3] for token in tokens for i in range(len(token) - 2)]
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
        # new features
#        ("desc_char2", TfidfVectorizer(
#            sublinear_tf=True,
#            strip_accents='unicode',
#            tokenizer=char_analyzer,
#            analyzer='word',
#            ngram_range=(1, 1),
#            max_features=16000,
#            preprocessor=get_col("description"))
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

# =============================================================================
# handle price
# =============================================================================
def feature_Eng_On_Price_Make_More_Cat(df):
    print('feature engineering -> on price and SEQ ...')    
    df["price"] = np.log(df["price"]+0.001).astype("float32") 
    df["price"].fillna(-1,inplace=True) 
    df["price+"] = np.round(df["price"]*2.8).astype(np.int16) # 4.8
    df["item_seq_number+"] = np.round(df["item_seq_number"]/100).astype(np.int16)
    
    # by steeve
    df['des_len_log'] = (np.log(df['description_num_chars']) * 4).astype(np.int8)
    df['des_nwords_log'] = (np.log1p(df['description_num_words']) * 20).astype(np.int8)
    return df
  
def feature_Eng_On_Deal_Prob(df, df_train):
    print('feature engineering -> on price deal prob +...')
    df2 = df
    
    # [465]   train's rmse: 0.161946  valid's rmse: 0.22738
    tmp = df_train.groupby(["price+"], as_index=False)['deal_probability'].median().rename(columns={'deal_probability':'median_deal_probability_price+'})     
    df = pd.merge(df, tmp, how='left', on=["price+"])
    df2['median_deal_probability_price+'] = df['median_deal_probability_price+']
    df2['median_deal_probability_price+'] =df2['median_deal_probability_price+'].astype(np.float32)
    del tmp; gc.collect()
    
    tmp = df_train.groupby(["param_2"], as_index=False)['deal_probability'].median().rename(columns={'deal_probability':'median_deal_probability_param_2'})     
    df = pd.merge(df, tmp, how='left', on=["param_2"])
    df2['median_deal_probability_param_2'] = df['median_deal_probability_param_2']
    df2['median_deal_probability_param_2'] =df2['median_deal_probability_param_2'].astype(np.float32)
    del tmp; gc.collect()
    
    tmp = df_train.groupby(["item_seq_number+"], as_index=False)['deal_probability'].median().rename(columns={'deal_probability':'median_deal_probability_item_seq_number+'})     
    df = pd.merge(df, tmp, how='left', on=["item_seq_number+"])
    df2['median_deal_probability_item_seq_number+'] = df['median_deal_probability_item_seq_number+']
    df2['median_deal_probability_item_seq_number+'] =df2['median_deal_probability_item_seq_number+'].astype(np.float32)
    del tmp; gc.collect()      
    return df2

del train_df, test_df; gc.collect()


# =============================================================================
# use additianl image data
# =============================================================================
feature_engineering(full_df)

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
full_df["population"] = full_df["population"].fillna(-1).astype(np.int32)
full_df["average_HLS_Hs"] = full_df["average_HLS_Hs"].astype(np.float32)
full_df["average_HLS_Ls"] = full_df["average_HLS_Ls"].astype(np.float32)
full_df["average_HLS_Ss"] = full_df["average_HLS_Ss"].astype(np.float32)
full_df["average_HSV_Ss"] = full_df["average_HSV_Ss"].astype(np.float32)
full_df["average_HSV_Vs"] = full_df["average_HSV_Vs"].astype(np.float32)
full_df["average_LUV_Ls"] = full_df["average_LUV_Ls"].astype(np.float32)
full_df["average_LUV_Us"] = full_df["average_LUV_Us"].astype(np.float32)
full_df["average_LUV_Vs"] = full_df["average_LUV_Vs"].astype(np.float32)
full_df["average_YUV_Us"] = full_df["average_YUV_Us"].astype(np.float32)
full_df["average_YUV_Vs"] = full_df["average_YUV_Vs"].astype(np.float32)
full_df["average_YUV_Ys"] = full_df["average_YUV_Ys"].astype(np.float32)

gc.collect()


from sklearn.model_selection import KFold
kf2 = KFold(n_splits=5, random_state=42, shuffle=True)
numIter = 0
rmse_sume = 0.
numLimit = 5

tmp = pd.DataFrame(full_df)
full_df_COPY = pd.DataFrame(tmp)
del tmp

for train_index, valid_index in kf2.split(y):
      numIter +=1
      print("training in fold " + str(numIter))
      
      if numIter>=numLimit+1:
            pass
      else:       
            full_df = pd.DataFrame(full_df_COPY)
            tmp = full_df[:len_train]
            train_df = tmp.iloc[train_index]
            del tmp;gc.collect()
                        
            # 不考虑使用均值
            try:
                  full_df.drop('median_deal_probability_price+', axis=1, inplace=True); gc.collect()
                  train_df.drop('median_deal_probability_price+', axis=1, inplace=True); gc.collect()
                  full_df.drop('median_deal_probability_param_2', axis=1, inplace=True); gc.collect()
                  train_df.drop('median_deal_probability_param_2', axis=1, inplace=True); gc.collect()
                  full_df.drop('median_deal_probability_item_seq_number+', axis=1, inplace=True); gc.collect()
                  train_df.drop('median_deal_probability_item_seq_number+', axis=1, inplace=True); gc.collect()
            except:
                  pass                  
            
            feature_Eng_On_Price_Make_More_Cat(full_df)
            feature_Eng_On_Price_Make_More_Cat(train_df)
            feature_Eng_On_Deal_Prob(full_df, train_df)
                        
            try:
                  full_df.drop('deal_probability', axis=1, inplace=True); gc.collect()
            except:
                  pass
            
            full_df, ready_full_df, tfvocab = data_vectorize(full_df)
            ready_df = ready_full_df
                        
            # NN Steeve
#            print("load nn oof 1 ...")
#            nn_oof_train = pd.read_csv('../input/emb_all_80_itseqcat_price_p4_pr1_catn_rg_ut_p_ict_pc_dll_dnl_rgb_apw_5fold_train.csv')
#            nn_oof_train.drop("user_id", axis=1, inplace=True)
#            nn_oof_test = pd.read_csv('../input/emb_all_80_itseqcat_price_p4_pr1_catn_rg_ut_p_ict_pc_dll_dnl_rgb_apw_5fold_test.csv')
#            
#            nn_oof_full = pd.concat([nn_oof_train, nn_oof_test])
#            nn_oof_full["nn_oof_1"] = nn_oof_full["deal_probability"]
#            del nn_oof_full["deal_probability"]
#            full_df = pd.merge(full_df, nn_oof_full, on='item_id', how='left')
#            del nn_oof_train, nn_oof_test
#            gc.collect()
#                       
#            # NN Zhuang
#            print("load nn oof 2 ...")
#            nn_oof_train = pd.read_csv('../input/res12_oof.csv')
#            nn_oof_train.drop("user_id", axis=1, inplace=True)
#            nn_oof_test = pd.read_csv('../input/res12.csv')
#            
#            nn_oof_full = pd.concat([nn_oof_train, nn_oof_test])
#            nn_oof_full["nn_oof_2"] = nn_oof_full["deal_probability"]
#            del nn_oof_full["deal_probability"]
#            full_df = pd.merge(full_df, nn_oof_full, on='item_id', how='left')
#            del nn_oof_train, nn_oof_test
#            gc.collect()
#
#            print("load xgb oof  ...")
#            xgb_oof_train = pd.read_csv('../input/ml_xgb_5fold_train_oof.csv')
#            xgb_oof_train.drop("user_id", axis=1, inplace=True)
#            xgb_oof_test = pd.read_csv('../input/ml_xgb_5fold_test.csv')
#            print(xgb_oof_train.shape)
#            print(xgb_oof_test.shape)
#            xgb_oof_full = pd.concat([xgb_oof_train, xgb_oof_test])
#            xgb_oof_full["xgb_oof"] = xgb_oof_full["deal_probability"]
#            del xgb_oof_full["deal_probability"]
#            full_df = pd.merge(full_df, xgb_oof_full, on='item_id', how='left')
#            del xgb_oof_train, xgb_oof_test
#            gc.collect()
#
#            print("load fm oof  ...")
#            fm_oof_train = pd.read_csv('../input/wordbatch_fmtrl_submission_train.csv')
#            print(fm_oof_train.shape)
#            fm_oof_train.drop("user_id", axis=1, inplace=True)
#            fm_oof_test = pd.read_csv('../input/wordbatch_fmtrl_submissionV3_5fold.csv')
#            print(fm_oof_test.shape)
#            fm_oof_full = pd.concat([fm_oof_train, fm_oof_test])
#            fm_oof_full["fm_oof"] = fm_oof_full["deal_probability"]
#            del fm_oof_full["deal_probability"]
#            full_df = pd.merge(full_df, fm_oof_full, on='item_id', how='left')
#            del fm_oof_train, fm_oof_test
#            gc.collect()
#
#            print("load yuki oof  ...")
#            yuki_oof_train = pd.read_csv('../input/oof_stacking_level1_lgbm_no_oof_xentropy_2_33000_train.csv')
#            yuki_oof_train.drop("user_id", axis=1, inplace=True)
#            yuki_oof_test = pd.read_csv('../input/oof_stacking_level1_lgbm_no_oof_xentropy_2_33000_test.csv')
#            yuki_oof_test.drop("user_id", axis=1, inplace=True)
#            print(yuki_oof_train.shape)
#            print(yuki_oof_test.shape)
#            yuki_oof_full = pd.concat([yuki_oof_train, yuki_oof_test])
#            yuki_oof_full["yuki_oof"] = yuki_oof_full["oof_stacking_level1_lgbm_no_oof_xentropy_2"]
#            del yuki_oof_full["oof_stacking_level1_lgbm_no_oof_xentropy_2"]
#            full_df = pd.merge(full_df, yuki_oof_full, on='item_id', how='left')
#            del yuki_oof_train, yuki_oof_test
#            gc.collect()
#
#            print("load catboost oof  ...")
#            catboost_oof_train = pd.read_csv('../input/catboost_submissionV2_train.csv')
#            print(catboost_oof_train.shape)
#            catboost_oof_train.drop("user_id", axis=1, inplace=True)
#            catboost_oof_test = pd.read_csv('../input/catboost_submissionV2_5fold.csv')
#            print(catboost_oof_test.shape)
#            catboost_oof_full = pd.concat([catboost_oof_train, catboost_oof_test])
#            catboost_oof_full["catboost_oof"] = catboost_oof_full["deal_probability"]
#            del catboost_oof_full["deal_probability"]
#            full_df = pd.merge(full_df, catboost_oof_full, on='item_id', how='left')
#            del catboost_oof_train, catboost_oof_test
#            gc.collect()
                                   
            from sklearn.cross_validation import KFold
            NFOLDS = 5#5
            SEED = 42
            kf = KFold(len_train, n_folds=NFOLDS, shuffle=True, random_state=SEED)
            
            # SGD
            from sklearn.linear_model import SGDRegressor
            sgdregressor_params = {'alpha':0.0001, 'random_state':SEED, 'tol':1e-3}
            sgd = SklearnWrapper(clf=SGDRegressor, seed = SEED, params = sgdregressor_params)
            FULL_DF = pd.DataFrame(full_df)
            FULL_DF.drop(["item_id"], axis=1, inplace=True)
            tmp1 = pd.DataFrame(full_df)
            tmp1.drop(["item_id"], axis=1, inplace=True)
            print('sgd 1 oof ...')
            sgd_oof_train, sgd_oof_test = get_oof(sgd, np.array(FULL_DF)[:len_train], y, np.array(FULL_DF)[len_train:])
            sgd_preds = np.concatenate([sgd_oof_train, sgd_oof_test])
            tmp1['sgd_preds_1'] = sgd_preds.astype(np.float32)
            tmp1['sgd_preds_1'].clip(0.0, 1.0, inplace=True)
            print('sgd 2 oof ...')
            sgd_oof_train, sgd_oof_test = get_oof(sgd, ready_df[:len_train], y, ready_df[len_train:])
            sgd_preds = np.concatenate([sgd_oof_train, sgd_oof_test])
            tmp1['sgd_preds_2'] = sgd_preds.astype(np.float32)
            tmp1['sgd_preds_2'].clip(0.0, 1.0, inplace=True)

            # Ridge
            #'alpha':20.0
            ridge_params = {'alpha':20.0, 'fit_intercept':True, 'normalize':False, 'copy_X':True,
                            'max_iter':None, 'tol':1e-3, 'solver':'auto', 'random_state':SEED}
            ridge = SklearnWrapper(clf=Ridge, seed = SEED, params = ridge_params)
            FULL_DF = pd.DataFrame(full_df)
            FULL_DF.drop(["item_id"], axis=1, inplace=True)
            tmp2 = pd.DataFrame(full_df)
            tmp2.drop(["item_id"], axis=1, inplace=True)
            print('ridge 1 oof ...')
            ridge_oof_train, ridge_oof_test = get_oof(ridge, np.array(FULL_DF)[:len_train], y, np.array(FULL_DF)[len_train:])
            ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
            tmp2['ridge_preds_1'] = ridge_preds.astype(np.float32)
            tmp2['ridge_preds_1'].clip(0.0, 1.0, inplace=True)
            print('ridge 2 oof ...')
            ridge_oof_train, ridge_oof_test = get_oof(ridge, ready_df[:len_train], y, ready_df[len_train:])
            ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
            tmp2['ridge_preds_2'] = ridge_preds.astype(np.float32)
            tmp2['ridge_preds_2'].clip(0.0, 1.0, inplace=True)

            ## Ridge
            ##'alpha':20.0
            ridge_params = {'alpha':10.0, 'fit_intercept':True, 'normalize':True, 'copy_X':True,
                            'max_iter':None, 'tol':1e-3, 'solver':'auto', 'random_state':SEED+2011}
            ridge = SklearnWrapper(clf=Ridge, seed = SEED, params = ridge_params)
            FULL_DF = pd.DataFrame(full_df)
            FULL_DF.drop(["item_id"], axis=1, inplace=True)
            tmp3 = pd.DataFrame(full_df)
            tmp3.drop(["item_id"], axis=1, inplace=True)
            print('ridge 1a oof ...')
            ridge_oof_train, ridge_oof_test = get_oof(ridge, np.array(FULL_DF)[:len_train], y, np.array(FULL_DF)[len_train:])
            ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
            tmp3['ridge_preds_1a'] = ridge_preds.astype(np.float32)
            tmp3['ridge_preds_1a'].clip(0.0, 1.0, inplace=True)
            print('ridge 2a oof ...')
            ridge_oof_train, ridge_oof_test = get_oof(ridge, ready_df[:len_train], y, ready_df[len_train:])
            ridge_preds = np.concatenate([ridge_oof_train, ridge_oof_test])
            tmp3['ridge_preds_2a'] = ridge_preds.astype(np.float32)
            tmp3['ridge_preds_2a'].clip(0.0, 1.0, inplace=True)
                        
            # 融入oof结果
            full_df['sgd_preds_1'] = tmp1['sgd_preds_1'].astype(np.float32)
            full_df['sgd_preds_2'] = tmp1['sgd_preds_2'].astype(np.float32)
            
            full_df['ridge_preds_1'] = tmp2['ridge_preds_1'].astype(np.float32)
            full_df['ridge_preds_2'] = tmp2['ridge_preds_2'].astype(np.float32)
            
            full_df['ridge_preds_1a'] = tmp3['ridge_preds_1a'].astype(np.float32)
            full_df['ridge_preds_2a'] = tmp3['ridge_preds_2a'].astype(np.float32)
            
            del tmp1, tmp2, tmp3
            del ridge_oof_train, ridge_oof_test, ridge_preds, ridge, sgd_oof_test, sgd_oof_train, sgd_preds, ready_df
            gc.collect()
                        

                        
            full_df.drop("item_id", axis=1, inplace=True)
            
            print("Modeling Stage ...")
            # Combine Dense Features with Sparse Text Bag of Words Features
            X = hstack([csr_matrix(full_df.iloc[:len_train]), ready_full_df[:len_train]]) # Sparse Matrix
            tfvocab = full_df.columns.tolist() + tfvocab
            X_test_full=full_df.iloc[len_train:]
            X_test_ready=ready_full_df[len_train:]
            del ready_full_df, full_df
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
                
            print("Modeling Stage ...")             
            X_train, X_valid = X.tocsr()[train_index], X.tocsr()[valid_index]
            y_train, y_valid = y.iloc[train_index], y.iloc[valid_index]            
            gc.collect()            
            lgbm_params =  {
#                    "gpu_platform_id":-1,
#                    "gpu_device_id":-1,
                    "tree_learner": "feature",    
                    "num_threads": 11,
                    "task": "train",
                    "boosting_type": "gbdt",
                    "objective": "regression",
                    "metric": "rmse",
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
                  
            del X_train, X_valid, y_train, y_valid, lgtrain, lgvalid, train_df
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


'''
[100]   train's rmse: 0.223448  valid's rmse: 0.226044
[200]   train's rmse: 0.215368  valid's rmse: 0.220678
[300]   train's rmse: 0.210236  valid's rmse: 0.218451
[400]   train's rmse: 0.206321  valid's rmse: 0.217242
[500]   train's rmse: 0.203286  valid's rmse: 0.216518
[600]   train's rmse: 0.200622  valid's rmse: 0.216053
[700]   train's rmse: 0.197905  valid's rmse: 0.215673
[800]   train's rmse: 0.195555  valid's rmse: 0.215386
[900]   train's rmse: 0.193417  valid's rmse: 0.215202
[1000]  train's rmse: 0.191389  valid's rmse: 0.215032
[1100]  train's rmse: 0.189498  valid's rmse: 0.2149
[1200]  train's rmse: 0.187679  valid's rmse: 0.214793
[1300]  train's rmse: 0.185923  valid's rmse: 0.214717
[1400]  train's rmse: 0.184341  valid's rmse: 0.214659
[1500]  train's rmse: 0.182768  valid's rmse: 0.214602
[1600]  train's rmse: 0.18126   valid's rmse: 0.21456
[1700]  train's rmse: 0.179751  valid's rmse: 0.214516
[1800]  train's rmse: 0.178466  valid's rmse: 0.214502
[1900]  train's rmse: 0.177197  valid's rmse: 0.214477
[2000]  train's rmse: 0.176008  valid's rmse: 0.214465
[2100]  train's rmse: 0.174849  valid's rmse: 0.214459
[2200]  train's rmse: 0.173684  valid's rmse: 0.214444
[2300]  train's rmse: 0.172603  valid's rmse: 0.21443
[2400]  train's rmse: 0.17159   valid's rmse: 0.214421
[2500]  train's rmse: 0.17055   valid's rmse: 0.214417
[2600]  train's rmse: 0.169536  valid's rmse: 0.214421
[2700]  train's rmse: 0.168509  valid's rmse: 0.214414
[2800]  train's rmse: 0.167543  valid's rmse: 0.214411
[2900]  train's rmse: 0.166565  valid's rmse: 0.21441
[3000]  train's rmse: 0.165634  valid's rmse: 0.214412
[3100]  train's rmse: 0.16472   valid's rmse: 0.214412
Early stopping, best iteration is:
[2933]  train's rmse: 0.166237  valid's rmse: 0.214407
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.21440662102548189
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
training in fold 2
feature engineering -> on price and SEQ ...
feature engineering -> on price and SEQ ...
feature engineering -> on price deal prob +...
/home/qifeng/avito/code/LGB_2193_plus_TE_20core_v10.py:783: RuntimeWarning: invalid value encountered in log
  df["price"] = np.log(df["price"]+0.001).astype("float32")
sgd 1 oof ...
sgd 2 oof ...
ridge 1 oof ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.939516902733002e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.519161941354815e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.2053547242159816e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.9354523477788703e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.526322694777041e-19 / 1.1102230246251565e-16
  RuntimeWarning)
ridge 2 oof ...
ridge 1a oof ...
ridge 2a oof ...
Modeling Stage ...
Feature Names Length:  1590799
Modeling Stage ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:1036: UserWarning: Using categorical_feature in Dataset.
  warnings.warn('Using categorical_feature in Dataset.')
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:681: UserWarning: categorical_feature in param dict is overrided.
  warnings.warn('categorical_feature in param dict is overrided.')
Training until validation scores don't improve for 200 rounds.
[100]   train's rmse: 0.223413  valid's rmse: 0.226329
[200]   train's rmse: 0.215257  valid's rmse: 0.221069
[300]   train's rmse: 0.210543  valid's rmse: 0.219114
[400]   train's rmse: 0.206955  valid's rmse: 0.218001
[500]   train's rmse: 0.203773  valid's rmse: 0.21723
[600]   train's rmse: 0.201011  valid's rmse: 0.216704
[700]   train's rmse: 0.198494  valid's rmse: 0.216349
[800]   train's rmse: 0.196151  valid's rmse: 0.216064
[900]   train's rmse: 0.19396   valid's rmse: 0.215816
[1000]  train's rmse: 0.19187   valid's rmse: 0.215628
[1100]  train's rmse: 0.189934  valid's rmse: 0.215491
[1200]  train's rmse: 0.188101  valid's rmse: 0.215368
[1300]  train's rmse: 0.186494  valid's rmse: 0.215303
[1400]  train's rmse: 0.184895  valid's rmse: 0.215218
[1500]  train's rmse: 0.18336   valid's rmse: 0.215151
[1600]  train's rmse: 0.181828  valid's rmse: 0.215106
[1700]  train's rmse: 0.180441  valid's rmse: 0.215069
[1800]  train's rmse: 0.179127  valid's rmse: 0.215024
[1900]  train's rmse: 0.177847  valid's rmse: 0.215002
[2000]  train's rmse: 0.176647  valid's rmse: 0.214977
[2100]  train's rmse: 0.175422  valid's rmse: 0.214959
[2200]  train's rmse: 0.174229  valid's rmse: 0.214931
[2300]  train's rmse: 0.173127  valid's rmse: 0.214925
[2400]  train's rmse: 0.172025  valid's rmse: 0.21492
[2500]  train's rmse: 0.170946  valid's rmse: 0.214907
[2600]  train's rmse: 0.169898  valid's rmse: 0.214909
[2700]  train's rmse: 0.168804  valid's rmse: 0.214904
[2800]  train's rmse: 0.167781  valid's rmse: 0.214904
[2900]  train's rmse: 0.166806  valid's rmse: 0.214895
[3000]  train's rmse: 0.165852  valid's rmse: 0.214895
[3100]  train's rmse: 0.164933  valid's rmse: 0.214893
[3200]  train's rmse: 0.163972  valid's rmse: 0.214896
[3300]  train's rmse: 0.163086  valid's rmse: 0.214901
Early stopping, best iteration is:
[3127]  train's rmse: 0.164672  valid's rmse: 0.214891
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.2148913106737893
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
training in fold 3
feature engineering -> on price and SEQ ...
feature engineering -> on price and SEQ ...
/home/qifeng/avito/code/LGB_2193_plus_TE_20core_v10.py:783: RuntimeWarning: invalid value encountered in log
  df["price"] = np.log(df["price"]+0.001).astype("float32")
feature engineering -> on price deal prob +...
sgd 1 oof ...
sgd 2 oof ...
ridge 1 oof ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.9397108575881986e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.5195378072404935e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.205648207583747e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.9359439749962917e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.5266268601324417e-19 / 1.1102230246251565e-16
  RuntimeWarning)
ridge 2 oof ...
ridge 1a oof ...
ridge 2a oof ...
Modeling Stage ...
Feature Names Length:  1590799
Modeling Stage ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:1036: UserWarning: Using categorical_feature in Dataset.
  warnings.warn('Using categorical_feature in Dataset.')
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:681: UserWarning: categorical_feature in param dict is overrided.
  warnings.warn('categorical_feature in param dict is overrided.')
Training until validation scores don't improve for 200 rounds.
[100]   train's rmse: 0.223826  valid's rmse: 0.226964
[200]   train's rmse: 0.215556  valid's rmse: 0.221428
[300]   train's rmse: 0.210852  valid's rmse: 0.219458
[400]   train's rmse: 0.207104  valid's rmse: 0.218303
[500]   train's rmse: 0.203859  valid's rmse: 0.21752
[600]   train's rmse: 0.200857  valid's rmse: 0.216972
[700]   train's rmse: 0.198248  valid's rmse: 0.216592
[800]   train's rmse: 0.195845  valid's rmse: 0.216291
[900]   train's rmse: 0.19371   valid's rmse: 0.216078
[1000]  train's rmse: 0.191609  valid's rmse: 0.215906
[1100]  train's rmse: 0.189704  valid's rmse: 0.215758
[1200]  train's rmse: 0.187937  valid's rmse: 0.215662
[1300]  train's rmse: 0.186184  valid's rmse: 0.215571
[1400]  train's rmse: 0.184579  valid's rmse: 0.215499
[1500]  train's rmse: 0.183096  valid's rmse: 0.215453
[1600]  train's rmse: 0.181571  valid's rmse: 0.215394
[1700]  train's rmse: 0.180186  valid's rmse: 0.215367
[1800]  train's rmse: 0.178831  valid's rmse: 0.215328
[1900]  train's rmse: 0.177492  valid's rmse: 0.215304
[2000]  train's rmse: 0.176268  valid's rmse: 0.215285
[2100]  train's rmse: 0.175084  valid's rmse: 0.215274
[2200]  train's rmse: 0.173893  valid's rmse: 0.215262
[2300]  train's rmse: 0.172803  valid's rmse: 0.215247
[2400]  train's rmse: 0.171731  valid's rmse: 0.215239
[2500]  train's rmse: 0.170688  valid's rmse: 0.215235
[2600]  train's rmse: 0.16961   valid's rmse: 0.21523
[2700]  train's rmse: 0.168609  valid's rmse: 0.215228
[2800]  train's rmse: 0.167608  valid's rmse: 0.215222
[2900]  train's rmse: 0.166628  valid's rmse: 0.215223
[3000]  train's rmse: 0.16569   valid's rmse: 0.215213
[3100]  train's rmse: 0.164732  valid's rmse: 0.215213
[3200]  train's rmse: 0.163795  valid's rmse: 0.215208
[3300]  train's rmse: 0.16287   valid's rmse: 0.21521
[3400]  train's rmse: 0.161974  valid's rmse: 0.21522
Early stopping, best iteration is:
[3203]  train's rmse: 0.163769  valid's rmse: 0.215207
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.21520707291638033
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
training in fold 4
feature engineering -> on price and SEQ ...
feature engineering -> on price and SEQ ...
/home/qifeng/avito/code/LGB_2193_plus_TE_20core_v10.py:783: RuntimeWarning: invalid value encountered in log
  df["price"] = np.log(df["price"]+0.001).astype("float32")
feature engineering -> on price deal prob +...
sgd 1 oof ...
sgd 2 oof ...
ridge 1 oof ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.939780524369426e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.519459175717141e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.205629659838124e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.935705111910435e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.5265796277243256e-19 / 1.1102230246251565e-16
  RuntimeWarning)
ridge 2 oof ...
ridge 1a oof ...
ridge 2a oof ...
Modeling Stage ...
Feature Names Length:  1590799
Modeling Stage ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:1036: UserWarning: Using categorical_feature in Dataset.
  warnings.warn('Using categorical_feature in Dataset.')
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:681: UserWarning: categorical_feature in param dict is overrided.
  warnings.warn('categorical_feature in param dict is overrided.')
Training until validation scores don't improve for 200 rounds.
[100]   train's rmse: 0.223797  valid's rmse: 0.226783
[200]   train's rmse: 0.215463  valid's rmse: 0.221345
[300]   train's rmse: 0.210857  valid's rmse: 0.219462
[400]   train's rmse: 0.206965  valid's rmse: 0.218203
[500]   train's rmse: 0.203643  valid's rmse: 0.217358
[600]   train's rmse: 0.200948  valid's rmse: 0.216893
[700]   train's rmse: 0.198522  valid's rmse: 0.216561
[800]   train's rmse: 0.19611   valid's rmse: 0.216282
[900]   train's rmse: 0.193832  valid's rmse: 0.216068
[1000]  train's rmse: 0.191808  valid's rmse: 0.215857
[1100]  train's rmse: 0.189868  valid's rmse: 0.215691
[1200]  train's rmse: 0.187995  valid's rmse: 0.215547
[1300]  train's rmse: 0.1863    valid's rmse: 0.215474
[1400]  train's rmse: 0.184607  valid's rmse: 0.215379
[1500]  train's rmse: 0.18309   valid's rmse: 0.215326
[1600]  train's rmse: 0.181609  valid's rmse: 0.215279
[1700]  train's rmse: 0.180164  valid's rmse: 0.215232
[1800]  train's rmse: 0.178802  valid's rmse: 0.215192
[1900]  train's rmse: 0.177518  valid's rmse: 0.215151
[2000]  train's rmse: 0.176269  valid's rmse: 0.215119
[2100]  train's rmse: 0.175055  valid's rmse: 0.215101
[2200]  train's rmse: 0.173913  valid's rmse: 0.215087
[2300]  train's rmse: 0.172849  valid's rmse: 0.215076
[2400]  train's rmse: 0.171794  valid's rmse: 0.215076
[2500]  train's rmse: 0.170733  valid's rmse: 0.215065
[2600]  train's rmse: 0.169664  valid's rmse: 0.215053
[2700]  train's rmse: 0.168605  valid's rmse: 0.21504
[2800]  train's rmse: 0.167622  valid's rmse: 0.215035
[2900]  train's rmse: 0.166629  valid's rmse: 0.215035
[3000]  train's rmse: 0.165665  valid's rmse: 0.21503
[3100]  train's rmse: 0.164752  valid's rmse: 0.215027
[3200]  train's rmse: 0.163877  valid's rmse: 0.215024
[3300]  train's rmse: 0.162948  valid's rmse: 0.215019
[3400]  train's rmse: 0.162073  valid's rmse: 0.215026
[3500]  train's rmse: 0.161182  valid's rmse: 0.215027
Early stopping, best iteration is:
[3303]  train's rmse: 0.162926  valid's rmse: 0.215018
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.2150181773601046
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
training in fold 5
feature engineering -> on price and SEQ ...
/home/qifeng/avito/code/LGB_2193_plus_TE_20core_v10.py:783: RuntimeWarning: invalid value encountered in log
  df["price"] = np.log(df["price"]+0.001).astype("float32")
feature engineering -> on price and SEQ ...
feature engineering -> on price deal prob +...
sgd 1 oof ...
sgd 2 oof ...
ridge 1 oof ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.9395472557744114e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.5192808683325063e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.20542164809439e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.935666900715387e-19 / 1.1102230246251565e-16
  RuntimeWarning)
/home/qifeng/anaconda3/lib/python3.6/site-packages/scipy/linalg/basic.py:40: RuntimeWarning: scipy.linalg.solve
Ill-conditioned matrix detected. Result is not guaranteed to be accurate.
Reciprocal condition number/precision: 2.5263634786428627e-19 / 1.1102230246251565e-16
  RuntimeWarning)
ridge 2 oof ...
ridge 1a oof ...
ridge 2a oof ...
Modeling Stage ...
Feature Names Length:  1590799
Modeling Stage ...
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:1036: UserWarning: Using categorical_feature in Dataset.
  warnings.warn('Using categorical_feature in Dataset.')
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:681: UserWarning: categorical_feature in param dict is overrided.
  warnings.warn('categorical_feature in param dict is overrided.')
Training until validation scores don't improve for 200 rounds.
[100]   train's rmse: 0.223896  valid's rmse: 0.226572
[200]   train's rmse: 0.215734  valid's rmse: 0.221231
[300]   train's rmse: 0.211013  valid's rmse: 0.219301
[400]   train's rmse: 0.207108  valid's rmse: 0.218213
[500]   train's rmse: 0.203891  valid's rmse: 0.217476
[600]   train's rmse: 0.2012    valid's rmse: 0.21707
[700]   train's rmse: 0.198596  valid's rmse: 0.216614
[800]   train's rmse: 0.196136  valid's rmse: 0.216282
[900]   train's rmse: 0.193958  valid's rmse: 0.216093
[1000]  train's rmse: 0.191914  valid's rmse: 0.215917
[1100]  train's rmse: 0.189962  valid's rmse: 0.215773
[1200]  train's rmse: 0.18813   valid's rmse: 0.215636
[1300]  train's rmse: 0.18646   valid's rmse: 0.215522
[1400]  train's rmse: 0.184854  valid's rmse: 0.21547
[1500]  train's rmse: 0.183322  valid's rmse: 0.215412
[1600]  train's rmse: 0.181805  valid's rmse: 0.215349
[1700]  train's rmse: 0.180409  valid's rmse: 0.21531
[1800]  train's rmse: 0.179031  valid's rmse: 0.215288
[1900]  train's rmse: 0.177768  valid's rmse: 0.215245
[2000]  train's rmse: 0.176529  valid's rmse: 0.215238
[2100]  train's rmse: 0.175323  valid's rmse: 0.215209
[2200]  train's rmse: 0.174154  valid's rmse: 0.215176
[2300]  train's rmse: 0.173034  valid's rmse: 0.21516
[2400]  train's rmse: 0.171991  valid's rmse: 0.215151
[2500]  train's rmse: 0.170992  valid's rmse: 0.215144
[2600]  train's rmse: 0.170016  valid's rmse: 0.215141
[2700]  train's rmse: 0.169027  valid's rmse: 0.215139
[2800]  train's rmse: 0.168098  valid's rmse: 0.215133
[2900]  train's rmse: 0.167133  valid's rmse: 0.215124
[3000]  train's rmse: 0.16616   valid's rmse: 0.215112
[3100]  train's rmse: 0.165238  valid's rmse: 0.21511
[3200]  train's rmse: 0.164293  valid's rmse: 0.215107
[3300]  train's rmse: 0.16341   valid's rmse: 0.215104
[3400]  train's rmse: 0.162512  valid's rmse: 0.2151
[3500]  train's rmse: 0.161651  valid's rmse: 0.215093
[3600]  train's rmse: 0.160798  valid's rmse: 0.2151
[3700]  train's rmse: 0.159978  valid's rmse: 0.21511
Early stopping, best iteration is:
[3509]  train's rmse: 0.161573  valid's rmse: 0.215091
save model ...
Model Evaluation Stage
calculating RMSE ...
RMSE: 0.21509064665650382
/home/qifeng/anaconda3/lib/python3.6/site-packages/lightgbm/basic.py:447: UserWarning: Converting data to scipy sparse matrix.
  warnings.warn('Converting data to scipy sparse matrix.')
calculating RMSE ...
mean rmse is: 0.214922765726452
Features importance...
                                feature       gain  split
96                        ridge_preds_2  12.059722  22298
28                          image_top_1   9.539342  86734
94                          sgd_preds_2   7.012684  24279
35                              param_1   5.915620  33802
21                                 city   5.282985  71724
95                        ridge_preds_1   2.777628  20786
97                       ridge_preds_1a   2.387205  18014
40                                price   2.137295  22176
18                        category_name   2.095923  18797
41                               region   1.669178  38419
36                              param_2   1.596180  17129
30                   image_top_1_impute   1.340697   4815
29  image_top_1_deal_probability_median   1.242934   6120
34                         n_user_items   1.220480  16388
38                 parent_category_name   0.970916   3661
42                              user_id   0.898259  11115
15                     avg_days_up_user   0.894924  17715
31             image_top_1_price_median   0.840249  11220
37                              param_3   0.840128  16795
33                      item_seq_number   0.759330  19948
16                    avg_times_up_user   0.665422  12932
39                           population   0.645119  18879
6                        average_LUV_Us   0.638290  18932
8                        average_YUV_Us   0.576945  17585
86                               price+   0.508950   2412
11                        average_blues   0.476276  16674
17                          blurinesses   0.476097  19305
3                        average_HSV_Ss   0.463573  18964
13                  average_pixel_width   0.460274  19998
91      median_deal_probability_param_2   0.458252   1992
0                        average_HLS_Hs   0.456728  18437
9                        average_YUV_Vs   0.453462  17139
1                        average_HLS_Ls   0.449799  14991
78                description_num_chars   0.449052  17497
4                        average_HSV_Vs   0.434097  16272
2                        average_HLS_Ss   0.403851  17397
70               text_feature_num_chars   0.403700   7482
7                        average_LUV_Vs   0.402938  16874
27                        image_quality   0.398595  17825
26                                image   0.398573  19324
98                       ridge_preds_2a   0.398398    711
14                         average_reds   0.395375  16746
10                       average_YUV_Ys   0.389383  14347
87                     item_seq_number+   0.378653   6275
5                        average_LUV_Ls   0.354885  13963
12                       average_greens   0.349001  13805
20           category_name_price_median   0.343143   4122
79                description_num_words   0.339825  12405
82                      title_num_chars   0.335383  13672
43                            user_type   0.329716   2783
All Done.

'''
