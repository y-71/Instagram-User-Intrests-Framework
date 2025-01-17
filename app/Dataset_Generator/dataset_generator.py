from context import Instagram
import pickle
import re
import json
from os import listdir
from os.path import isfile, join
from time import sleep
import pandas as pd
from caption_formater import extract_hash_tags , remove_hash_tags , deEmojify

import igramscraper
from retrive_data import get_dataframe , get_all_files
import progressbar

account_names_path="../../dataset/account_names/"
output_path="../../dataset/collected_data/"
instagram = Instagram()
threshhold = 8000
columns = {"photo_url": 0, "captions": 1, "hashtags": 2, "interest": 3}
data = []
checkpoint_filename="./checkpoint.txt"
flag_for_instagram_exception=0


    

def get_medias(account,threshhold,current_file_start_index,current_index):
    try :
        
        account_attributes = instagram.get_account(account)
        media_count = account_attributes.media_count
        post_number = min(media_count,threshhold)
        print(media_count)
        medias = instagram.get_medias(account, post_number)
        #sleep(30)
        return medias
    except igramscraper.exception.instagram_exception.InstagramException as e :
        """
            when recieving this exception we save the current_index which represents 
            the last non processed index so we process it in next iteration

        """
        print(e)
        #YOUR CODE HERE
        current_file_start_index=str(current_file_start_index)+'\n'
        current_index=str(current_index)
        update_checkpoint(current_file_start_index,current_index)
        global flag_for_instagram_exception 
        flag_for_instagram_exception = 1
        return None
        
    except Exception as e:
        print(e)
        #YOUR CODE HERE
        current_file_start_index=str(current_file_start_index)+'\n'
        next_index=str(current_index+1)
        update_checkpoint(current_file_start_index,next_index)
        return None
    


def create_post(media, columns, interest):
    post = [0 for i in columns.keys()]
    post[columns['interest']] = str(interest).lower()
    post[columns['photo_url']] = str(media.image_high_resolution_url) #high_res
    caption = None
    caption = deEmojify(media.caption)
    post[columns['captions']] = remove_hash_tags(caption)
    post[columns['hashtags']] = extract_hash_tags(caption)
    return post




def generate_dataframe(input_filename,current_file_start_index,start_index):
    global flag_for_instagram_exception
    file = open(input_filename, "r", encoding = "utf-8")
    Lines = file.readlines()
    #print(Lines)
    print ('scrapping...')
    interest = input_filename.replace(account_names_path,'')
    current_index=start_index
    
    if int(current_index)>= len(Lines):
        current_file_start_index=current_file_start_index+1
        current_index=str(0)
        current_file_start_index=str(current_file_start_index)+'\n'
        update_checkpoint(current_file_start_index,current_index)
        return interest
    
    
    for line in Lines[start_index:]:
        account = line[:-1].split(' ')[0]  
        post = []
        medias=get_medias(account,threshhold,current_file_start_index,current_index)
        #______________________ We got Medias
        current_index=current_index+1
            
        if medias!=None:
            ## Logging account 
            print("interest : "+interest+"\n")
            print("account name : "+account+"\n")            
            with progressbar.ProgressBar(max_value=len(medias)) as bar:
                for i in range(len(medias)):
                    #Creating a new row
                    post = create_post(medias[i], columns, interest)
                    data.append(post)
                    ## updating bar
                    bar.update(i)
                #dataset[account] = user
        else:
            if (flag_for_instagram_exception == 1):
                return interest
            #break
            
    if int(current_index)>= len(Lines):
        '''if all medias of this interest are dowloaded initialise 
            the start_index and file_start_index in checkpoint file'''
            
        current_file_start_index=current_file_start_index+1
        current_index=str(0)
        current_file_start_index=str(current_file_start_index)+'\n'
   
        update_checkpoint(current_file_start_index,current_index)
    
        return interest
    
    file.close()
    return interest



def laod_data_into_dataframe(start_index,output_file_added_to_path):
    new_dataframe = pd.DataFrame(data=data, columns=columns)
    if (start_index!=0) and (isfile(output_file_added_to_path)):
        df = get_dataframe(output_file_added_to_path)
        df = df.append(new_dataframe, ignore_index = True)
        return df
    else :
        return new_dataframe


def update_checkpoint(current_file_start_index,current_index):
    checkpoint_file=open(checkpoint_filename,'w')
    checkpoint_file.truncate(0)
    checkpoint_file.write(current_file_start_index)
    checkpoint_file.write(current_index)
        

def make_output_file(input_file):
    output_file=input_file+".csv"
    output_file_added_to_path=output_path+output_file
    return output_file_added_to_path        

def load_checkpoint():
    checkPoint_file = open(checkpoint_filename, "r", encoding = "utf-8")
    Lines = checkPoint_file.readlines()
    file_start_index=0
    start_index=0
    if len(Lines)==2:
        '''get file_start_undex and start_index from checkpoint file'''
        file_start_index=int(Lines[0])
        start_index=int(Lines[1])
    print("loading checkpoint")
    print("your file index from the list "+str(file_start_index))   
    print("your start index in file "+str(start_index))
    return file_start_index,start_index

def generate():
    global flag_for_instagram_exception 
    #input_files = get_all_files()
    input_filenames = get_all_files(account_names_path)
    #Use Second Line In case you want to get all files
    #input_filenames = ['Industry','Outdoors']
    #input_files=["shopping and  fashion"]
    ''' we will retrieve name last_file processed with it's start_index from checkpoint file'''
    #________________file_start_index = line in file
    #________________start_index = the file we're using 
    
    file_start_index,start_index=load_checkpoint()
    #input_files=["shopping and  fashion"]
    #print(input_files)
    current_file_start_index=file_start_index
    if current_file_start_index >= len(input_filenames):
        exit()
    for input_filename in input_filenames[file_start_index:] :
        data=[]
        input_file=account_names_path+input_filename
        print("input file :"+input_file )
        try:
            '''  if it's not the first iteration we should retrieve start_index '''
            checkPoint_file = open(checkpoint_filename, "r", encoding = "utf-8")
            Lines = checkPoint_file.readlines()
            start_index=0
            if len(Lines)==2:
                start_index=Lines[1]
            start_index=int(start_index)
            
            interest=generate_dataframe(input_file,current_file_start_index,start_index)
            
            output_file=make_output_file(input_filename)
            df=laod_data_into_dataframe(start_index, output_file )
            print("Dataset generated")
            print(df.info())
            #with open(output_file_added_to_path, 'w', encoding='utf-8') as f:
            df.to_csv(output_file)
            #cleaning the data array
            if flag_for_instagram_exception==1:
                exit()
        except igramscraper.exception.instagram_exception.InstagramException as e :
            print("Try an hour after")
            exit()
        except Exception as e:
            print(e)
    
        current_file_start_index=current_file_start_index+1


if __name__=="__main__":
    while True :
        generate()
        sleep(60*10)




#Problems:
#high_res image always available?
#hash tag functions testing
    """
    #__testing progressbar
    for i in progressbar.progressbar(range(100)):
        sleep(0.02)
    """

    """
        ---Here We tried Handling this exception by creating a session pool 
        It didn't work

    except igramscraper.exception.instagram_exception.InstagramException :
        try:
            instagram=connect()  
            account_attributes = instagram.get_account(account)
            media_count = account_attributes.media_count
            post_number = min(media_count,threshhold)
            print(media_count)
            medias = instagram.get_medias(account, post_number)
            #sleep(30)
            
            return medias 
        except Exception as e:
            print(e)
            return None
    """
