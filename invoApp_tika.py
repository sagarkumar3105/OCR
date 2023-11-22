import streamlit as st
import re
import tika
from tika import parser
import pandas as pd
import numpy as np
import cv2
import re
import pandas as pd
# import fitz
# import json
import os


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
        
    vendorList=[vendor.upper()]*len(dog)
    masterData=dict(zip(head,[vendor,date,invoNum,dog,hsn,qty,rate,per,amt]))
    ledgerData=dict(zip(head[1:],[date,invoNum,dog,hsn,qty,rate,per,amt]))
    #data[vendor[0]]=data
    
    mdf=pd.DataFrame(masterData)
    mdf.to_csv("MasterData.csv",mode='a',index=False,header=False)
    
    ldf=pd.DataFrame(ledgerData)
    ldf.to_csv("Ledgers/"+vendor.upper()+".csv",mode='a',index=False,header=False)
    #df.to_json("Invo_res.json")
    
def kpkTemplate(dataList):
    pronumIdx=findIdx(".*pro no.*",dataList,0)
    invoiceDateIdx=findIdx(".*[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4}.*",dataList,0)
    ponumIdx=findIdx(".*po.*",dataList,1)
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

    data=[pronum,invoiceDate,ponum,total,gst,net]
    #print(data)
    data2=[]
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
        row=["KPK_SCIENTIFIC_SUPPLIES",invoiceDate,pronum,prod,"",unit,rate,'',amt]
        data2.append(row)
    return data,data2


# def imProcess(fname):
    # doc = fitz.open(fname)
    # for i in range(doc.page_count):
        # page=doc.load_page(i)
        # #page.clean_contents()
        # pageText=page.get_text("text") 
        
        # pix=page.get_pixmap(dpi=180)
        
        # pimg = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        # img=np.asarray(pimg)

        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # img = cv2.bitwise_not(gray)
        # # cv2.imshow("xyz",img)
        # # cv2.waitKey(0)
  
        # # cv2.destroyAllWindows()
        
        # text = pytesseract.image_to_string(img,config='-c preserve_interword_spaces=0 --psm 4')

        # dl=text.split("\n")
        # endPtrn=re.compile("Output CGST.*",re.I)

        # # print("-------should be>",dl.index("Output CGST @9 % 9 % 111.48"))
        # vendor=''
        # date=''
        # invoNum=''  
        
        # tableStartPtrn=re.compile(".*Description of Goods.*")
        # tableStartIdx=[dl.index(i) for i in list(filter(tableStartPtrn.match,dl))][0]
        
        
        # if(i==0):          
            # vendor=" ".join(dl[2].split(" ")[:-3])
            # dtPtrn=re.compile(".*[0-9]{1,2}-[A-Za-z]+-[0-9]{2,4}.")
            # date=list(filter(dtPtrn.match,dl))[0].split(" ")[-1]
            # invoNum=list(filter(dtPtrn.match,dl))[0].split(" ")[-2]
            # dl=dl[tableStartIdx:]
            # try:
                # endIdx=[dl.index(i) for i in list(filter(endPtrn.match,dl))][0]
                # dl=dl[:endIdx-1]
            # except IndexError:
                # pass

        # if(i>0):
            # dl=dl[tableStartIdx:]
            # endIdx=[dl.index(i) for i in list(filter(endPtrn.match,dl))][0]
            # dl=dl[:endIdx-1]
            
            
        # getTableDate(dl,vendor,date,invoNum)
        
        # print(text)
        # return text
        
#txt=imProcess("jainchem.pdf")




def user():
    st.title("Invoice Proecessing System")
    ufiles=st.file_uploader("Upload a pdf file",accept_multiple_files=True)
    go=st.button("Process")
    kpk=re.compile(".*kpk.*",re.IGNORECASE)  

    if(go):
        # try:
            for f in ufiles:
                doc=''
                try:
                    doc=parser.from_file(f) # Reading the PDF File
                except:
                    st.error("File Rendering failed Contact Developer")
                res=doc['content']
                dataList=res.split("\n")
                #imProcess(f)#"jainchem.pdf")#r"../Main Demo/invo.png")
                dataList=[i.strip() for i in dataList if len(i.strip())>0] # Removing all empty lines and removing trailing spaces
                if len(tuple(filter(kpk.match, dataList))):
                    #data=[pronum,invoiceDate,ponum,total,gst,net]
                    head1=["PRO Num","Date","PO Num","Total","GST @18%","Net Amount"]
                    head2=['Vendor','Date','Invoice Number','Description of Goods','HSN/SAC','Quantity','Rate','per','Amount']
                    data1,data2=kpkTemplate(dataList)
                        
                    dfData1=dict(zip(head1,data1)) # Puting all the extracted data into respective columns
                    kpkDf1=pd.DataFrame(dfData1,index=[0])
                    kpkDf1.to_csv(r"Ledgers\KPK_SCIENTIFIC_SUPPLIES.csv",mode='a',index=False,header=False) #Writing the data
                    tempdf=[] #Container to hold each row of invoice
                    for d in data2:
                        tempdf.append(dict(zip(head2,d)))
                    data2=tempdf
                    kpkDf2=pd.DataFrame(data2,index=range(len(data2)))
                    kpkDf2.to_csv(r"MasterData.csv",mode='a',index=False,header=False)
                else:
                    st.warning("Got a new invoice Type")
            st.success("Details Extracted")
        # except e:
            # st.error("Check the file Formate. The uploaded file doens't follow the predescribed formate")
#@st.cache()
# def getvName(led):
    # return st.multiselect("Select the vendor Name",led)
#@st.cache(suppress_st_warning=True)
# def Authenticate():
    
    # return session
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
        st.markdown("**Session Authenticated**")
        if not os.path.isfile("/Ledgers/"):
            os.makedirs("Ledgers", exist_ok=True)
        led=[i.split(".")[0] for i in os.listdir("Ledgers/")]

        st.info("Total Number of Available Ledgers/Vendors: "+str(len(led)))

        vName=st.multiselect("Select the vendor Name",led)
        #getvName(led)
        df=pd.read_csv("MasterData.csv")
        res=pd.DataFrame(columns=df.columns.tolist())
        #show=st.button('show')
        #if show:
        saveFileName=''
        exportButton=''
        with st.expander("Export File"):
            saveFileName=st.text_input("Enter a file name to export the below result as CSV")
            exportButton=st.button("Export")
        for i in vName:
            res=pd.concat([res,df[df['Vendor']==i]])
        st.dataframe(res)
        if(exportButton):
            res.to_csv(saveFileName+".csv")
            st.balloons()#("File saved in local machine")
        
        
    else:
        st.warning("Please Login First")

t1,t2=st.tabs(['User','Admin'])
with t1:
    user()

with t2:
    admin()
