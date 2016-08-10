import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

class Tempereture:

    @staticmethod
    def compute(specter,lines):
        h=6.62606957*10**-34
        c=3*10**8
        kb=1.3806488*10**-23

        tempData={'Ek':[],'nkgk':[]}
        koef=[]
        temp=0

        for key, line in enumerate(lines):
            intLine = sp.trapz(specter[line[0]:line[1]])

            lambdaNist=line[2]
            Aki=line[3]
            Ek=line[4]
            g=line[5]
            if intLine>0:
                nkgk=np.log(intLine/((h*c*g*Aki*10**8)/(lambdaNist*10**-9)))
                tempData['Ek'].append(Ek)
                tempData['nkgk'].append(nkgk)


        if len(tempData['Ek'])>0 and len(tempData['nkgk'])>0:

            koef=np.polyfit(tempData['Ek'], tempData['nkgk'], 1)
            temp=-koef[0]

        return (tempData,koef,temp)
