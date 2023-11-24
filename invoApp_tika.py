import streamlit as st
import re
import tika
from tika import parser
import pandas as pd
import numpy as np
import re
import pandas as pd
import json
import os

#os.environ['PATH']=f'''os.environ.get("PATH","")"C:\\Users\\Sagar Kumar\\Documents\\NYL Technology\\OCR Envo\\Tesseract-OCR"'''

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://sagarinvoapp:fT5fr@cluster0.sap1yb0.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db=client["Cluster0"]
print(db.list_collection_names())

def findAllIdx(exp,tlist):
    pattern=re.compile(exp,re.I)
    try:
        return [tlist.index(i) for i in list(filter(pattern.match,tlist))] #List comprehensions are faster
    except IndexError:
        return []

def findIdx(exp,tlist,pos=-1):
    pattern=re.compile(exp,re.I)
    try:
        return [tlist.index(i) for i in list(filter(pattern.match,tlist))][pos] #List comprehensions are faster
    except IndexError:
        return []

def writeJsonJainChem():
        data=dict()
        itemList=[]
        for i in range(len(dog)):
            itemData=dict()
            itemData['Description of Goods']=dog[i]
            itemData['HSN/SAC']=hsn[i]
            itemData['Quantity']=qty[i]
            itemData['Rate']= rate[i]
            itemData['per'] =per[i]
            itemData['Amount']=amt[i]
            itemList.append(itemData)
        data[vendor[0]]=itemList
        jd=json.dumps(data,indent=4)
        with open("invo_res.json","a") as f:
            f.write(jd)

def jainChemTemplate(dl,date,invoNum):
    print("!!!!!!!!!!!!!!!!!!!")
    vendor='Jain Chemicals'
    head=['Vendor','Date','Invoice Number','Description of Goods', 'HSN/SAC', 'Quantity', 'Rate', 'per', 'Amount']
    dog=[]
    hsn=[]
    qty=[]
    rate=[]
    per=[]
    amt=[]
    for r in dl[1:]:
        r=r.split(" ")
        print(r,"\n")
        if(r[-4].lower()!='nos' and r[-4].lower()!='nos.' and r[-4].lower()!='kgs' and r[-4].lower()!='kgs.'):
            t=re.split('(\d+)',r[-4])
            r[-4]=t[-1]
            r.insert(-4,t[-2])
            #print("SPECIAL ----> ",r)
            
        if(r[-6].isdigit()):
            hsn.append(r[-6])
            dog.append(" ".join(r[:-6]))
        else:
            hsn.append("")
            dog.append(" ".join(r[:-5]))
        
       
            
        qty.append(" ".join(r[-5:-3]))
        rate.append(r[-3])
        per.append(r[-2])
        amt.append(r[-1])
    
    ledgerData={"Date":date,"Invoice Number":invoNum,'Description of Goods':dog, 'HSN/SAC':hsn, 'Quantity':qty, 'Rate':rate, 'per':per, 'Amount':amt}
    masterData={"Jain Chemicals":ledgerData}

    writeToDb("jainChemicals",ledgerData,masterData)
    #vendorList=[vendor.upper()]*len(dog)
    # masterData=dict(zip(head,[vendor,date,invoNum,dog,hsn,qty,rate,per,amt]))
    # ledgerData=dict(zip(head[1:],[date,invoNum,dog,hsn,qty,rate,per,amt]))
    #data[vendor[0]]=data
    
    # mdf=pd.DataFrame(masterData)
    # mdf.to_csv("MasterData.csv",mode='a',index=False,header=False)
    
    # ldf=pd.DataFrame(ledgerData)
    # ldf.to_csv("Ledgers/"+vendor.upper()+".csv",mode='a',index=False,header=False)
    #df.to_json("Invo_res.json")

def writeToDb(tableName,tableData,MasterData):
    global db
    db[tableName].insert_one(tableData)
    db["MasterData"].insert_one(MasterData)
    print("inster Record")

 
def kpkTemplate(dataList):
    pronumIdx=findIdx(".*pro no.*",dataList,0)
    invoiceDateIdx=findIdx(".*[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4}.*",dataList,0)
    ponumIdx=findIdx(".*po.*",dataList,0)
    tableHeaderIdx=findIdx(".*CAT NO PRODUCT NAME.*",dataList,0)
    totalIdx=findIdx(".*Total.*",dataList,)
    gstIdx=findIdx(".*gst.*",dataList)
    netIdx=findIdx(".*net amount.*",dataList)

    pronum=dataList[pronumIdx].split()[-1]
    invoiceDate=dataList[invoiceDateIdx].split()[-1]
    ponum=dataList[ponumIdx][6:]
    total=dataList[totalIdx].split()[-1]
    gst=dataList[gstIdx].split()[-1]
    net=dataList[netIdx].split()[-1]

    dataList=dataList[tableHeaderIdx+1:totalIdx]
    data2=[]
    prodList=[]
    qtyList=[]
    amtList=[]
    rateList=[]
    unitList=[]
    for d in dataList:
        line=d.split()
        amt=line[-1]
        qty=line[-2]
        rate=line[-3]
        unit=''
        #per=''
        k=None
        if "PACK" in line or "PKT" in line:
            unit=line[-4]
            #per=line[-4]
            k=-4
        else:
            unit=line[-5]
            #per=line[-4]
            k=-5
        prod=" ".join(line[0:k])[2:]
        prod=re.sub(r'[^\w\s\(\)]', "", prod)
        #row=["KPK_SCIENTIFIC_SUPPLIES",invoiceDate,pronum,prod,"",unit,rate,'',amt]
        #data2.append(row)
        prodList.append(prod)
        qtyList.append(qty)
        amtList.append(amt)
        rateList.append(rate)
        unitList.append(unit)

    ledgerData={"PRO Num":pronum,"Date":invoiceDate,"PO Num":ponum,"Total":total,"GST @18%":gst,"Net Amount":net}
    masterData={"KPK_SCIENTIFIC_SUPPLIES":{'Date':invoiceDate,'Invoice Number':ponum,'Description of Goods':prodList,'HSN/SAC':["" for _ in range(len(prodList))],'Quantity':qtyList,'Rate':rateList,'per':unitList,'Amount':amtList}}

    writeToDb("KPKScientificSupplies_002",ledgerData,masterData)



#------------------------------>client.close()


def user():
    st.title("Invoice Processing System")
    ufiles=st.file_uploader("Upload a PDF file",accept_multiple_files=True)
    go=st.button("Process")
    kpk=re.compile(".*kpk.*",re.IGNORECASE)  
    successPrompt="Details Extracted"
    if(go and ufiles):
        # try:
            for f in ufiles:
                doc=''
                try:
                    doc=parser.from_file(f) # Reading the PDF File
                    print("!!!!!!")
                except:
                    st.error("File Rendering failed Contact Developer")
                res=doc['content']
                
                dataList=res.split("\n")
                #imProcess(f)#"jainchem.pdf")#r"../Main Demo/invo.png")
                dataList=[i.strip() for i in dataList if len(i.strip())>0] # Removing all empty lines and removing trailing spaces
                if len(tuple(filter(kpk.match, dataList))):
                    #data=[pronum,invoiceDate,ponum,total,gst,net]
                    kpkTemplate(dataList)
                else:
                    
                    st.warning("Got a new invoice Type")
                    successPrompt="!!! Details Not Extracted"
            st.success(successPrompt)


def admin():
    st.title("Admin Portal")
    session=False
    with st.sidebar:
        uname=st.text_input("Enter User name")
        pas=st.text_input("Enter Password",type="password")
        st.caption("Click Enter to login")
        if(uname=="admin" and pas=="admin"):
            st.success("Authenticated")
            session=True
        else:
            st.error("Permission denied. Try with correct credentials")
    
    if session:
        global db
        st.markdown("**Session Authenticated**")
        listOfAllLedgers=db.list_collection_names()
        listOfAllLedgers.remove("MasterData")
        numOfLedgers=len(listOfAllLedgers)
        st.info("Total Number of Available Ledgers/Vendors: "+str(numOfLedgers))

        vName=st.multiselect("Select the vendor Name",listOfAllLedgers)
        
        col1,col2=st.columns(2)
        viewButton=None
        
        with col1:
            viewButton=st.button("View Ledger")
        with col2:
            eraseButton=st.button("Erase All")
            if eraseButton:
                for name in listOfAllLedgers:
                    db[name].drop()
        list_cur=[]
        for name in vName:
            collection=db[name]
            cursor=collection.find()
            list_cur.append(list(cursor))
        
        if viewButton:
            st.write(list_cur)
        #mess=pd.DataFrame()
        #for i in range(len(list_cur)):
        # df = json_normalize(list_cur).drop("_id",axis=1)#[i]#)#.astype({"_id": str})
        # st.write(df)
        # for series_name,series in df.items():
        #     print(series)


        #df.columns = df.columns.str.replace('.', '_')
        #st.table(df)

            


        # json_data = dumps(list_cur, indent = 2)  
        # st.write(json_data)
        # df=pd.read_csv("MasterData.csv")
        # res=pd.DataFrame(columns=df.columns.tolist())
        # #show=st.button('show')
        # #if show:
        # saveFileName=''
        # exportButton=''
        # with st.expander("Export File"):
        #     saveFileName=st.text_input("Enter a file name to export the below result as CSV")
        #     exportButton=st.button("Export")
        # for i in vName:
        #     res=pd.concat([res,df[df['Vendor']==i]])
        # st.dataframe(res)
        # if(exportButton):
        #     res.to_csv(saveFileName+".csv")
        #     st.balloons()#("File saved in local machine")
        
        
    else:
        st.warning("Please Login First")

t1,t2=st.tabs(['User','Admin'])
with t1:
    user()

with t2:
    admin()
