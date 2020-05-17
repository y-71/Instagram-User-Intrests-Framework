import json
import pandas as pd
import hashtags as ht
filename = 'technology.csv'

def retrive_data(filename):
    try:
        df=pd.read_csv(filename)
        return df
    except Exception as e:
            print(e)

def remove_hashtags():
    pass

def clean_data():
    df=retrive_data(filename)
    #print(df.captions.apply(ht.remove_hashtags(lambda x : remove_hashtags(str(x)))))
    df.captions.str.findall(r'#.*?(?=\s|$)')

if __name__=="__main__":
    clean_data()
    