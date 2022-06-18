import readData as rd
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate
from sklearn.metrics import confusion_matrix
from sklearn.metrics import multilabel_confusion_matrix

import warnings
def warn(*args, **kwargs):
    pass
warnings.warn = warn

#Leemos los datos de los distintos archivos
ydata_table = []
affirdt = rd.load_affirm_target()
ydata_table.append(["Affirmación",affirdt.value_counts()])

condt = rd.load_cond_target()
ydata_table.append(["Condicional",condt.value_counts()])

doubtqt = rd.load_doubtq_target()
ydata_table.append(["Duda",doubtqt.value_counts()])

empht = rd.load_emphasis_target()
ydata_table.append(["Énfasis",empht.value_counts()])

negt = rd.load_neg_target()
ydata_table.append(["Negación",negt.value_counts()])

relt = rd.load_rel_target()
ydata_table.append(["Relativa", relt.value_counts()])

topicst = rd.load_topics_target()
ydata_table.append(["Tópicos",topicst.value_counts()])

wht = rd.load_wh_target()
ydata_table.append(["Preguntas abiertas",wht.value_counts()])

ynt = rd.load_yn_target()
ydata_table.append(["Preguntas cerradas",ynt.value_counts()])

print("###################### Tabla de distribución #####################")
table = PrettyTable()
table.field_names = ["Clase", "Negativo", "Positivo"]
for data in ydata_table:
    table.add_row([data[0],data[1][0],data[1][1]])

print(table)
print("################### FIN Tabla de distribución #####################")

#Concatenamos los ejemplos en una misma tabla
# data = pd.concat([affirdd,condd,doubtqd,emphd,negd,reld,topicsd,whd,ynd], ignore_index=True)
data = rd.readAll(user="All",targets=False)
print("############# Verificamos correcta lectura de datos ###########")
print(data)
print("###############################################################")

print("############ Quitamos la etiqueta temporal de cada dato #######")
data.drop('0.0',axis=1,inplace=True)
print("###############################################################")

print("################ Buscamos datos faltantes ###################")
print("Número de datos faltantes:\n", data.isnull().sum())
print("#############################################################")

#Concatenamos las etiquetas en una tabla
# y = pd.concat([affirdt,condt,doubtqt,empht,negt,relt,topicst,wht,ynt], ignore_index=True)
y = rd.readAll(user="All",targets=True)

#Dividimos en train y test
X_train,X_test,y_train,y_test = train_test_split(data.iloc[:,1:],y,stratify=y)

# Verificamos la distribución de datos obtenidas en training
y_train = np.ravel(y_train)
print("################# Distribución Training Entre Casos Positivos ###############")
sns.histplot(y_train[np.where(y_train>0)],kde=True)
plt.title("Distribución Training Entre Casos Positivos")
plt.show()
string = input("Press any key to continue")
print("#####################################################################")
print("######################### Distribución Training Total ########################")
sns.histplot(y_train[np.where(y_train>=0)],kde=True)
plt.title("Distribución Training Total")
plt.show()
string = input("Press any key to continue")
print("#####################################################################")

#Escalado
scaler = StandardScaler()
scaler.fit(X_train)
X_train = pd.DataFrame(scaler.transform(X_train))
X_test = pd.DataFrame(scaler.transform(X_test))

y_train = np.ravel(y_train)

print("################ Búscando Hiperparámetros RL ###################")
parametersLR = {'penalty':['l1'], 'solver': ['saga'], 'C': [0.1],
              'max_iter':[100]}
scoring = ['f1_micro','roc_auc_ovr']

h_models = []
total = 1
for i in parametersLR.keys():
    total = total * len(parametersLR[i])

cont = 0
lr_models_table = PrettyTable()
lr_models_table.field_names = ["Parámetros","Media F1","Media AUC_ROC"]
maximo = -1
for C in parametersLR['C']:
    for t in parametersLR['max_iter']:
        for p in parametersLR['penalty']:
            for s in parametersLR['solver']:
                RL =  LogisticRegression(C=C,max_iter=t,penalty=p,solver=s,
                                         multi_class='multinomial',n_jobs=2)
                cv_results = cross_validate(RL,X_train,y_train,cv=5,scoring=scoring)
                h_models.append(RL)
                par = "C="+ str(C) + " maxIter=" + str(t) + " \npenalty=" + str(p) + " solver=" + s
                lr_models_table.add_row([par,cv_results['test_f1_micro'].mean(),cv_results['test_roc_auc_ovr'].mean()])
                if maximo < cv_results['test_roc_auc_ovr'].mean():
                    maximo = cv_results['test_roc_auc_ovr'].mean()
                    max_p  = {'C':C,'solver':'saga','max_iter':t,'penalty':p}
                # print(RL.score(X_train,y_train))
            cont = cont + 1
            # print(cont/total*'=>',end='')
print("############## Resultados Obtenidos ##############")
print(lr_models_table)
print("################ FIN Búsqueda RL ###################")

RLf = LogisticRegression(C=max_p['C'],max_iter=max_p['max_iter'], penalty=max_p['penalty'],
                        solver=max_p['solver'], multi_class='multinomial',n_jobs=2)
#RLf = LogisticRegression(multi_class='multinomial')
RLf.fit(X_train,y_train)
y_pred = RLf.predict(X_train)
# matrix = multilabel_confusion_matrix(y_train,y_pred)

rd.Cmatrix_and_percentages(y_train,y_pred,title="Regresión Logística")

print("################ Error Baseline Moda ###################")
baseline0 = DummyClassifier(strategy="most_frequent")
cv_results = cross_validate(baseline0,X_train,y_train,cv=5,scoring=scoring)
dummy_model_table = PrettyTable()
dummy_model_table.field_names = ["Parámetros", "Media F1", "Media AUC_ROC"]
dummy_model_table.add_row(["Moda",cv_results['test_f1_micro'].mean(),cv_results['test_roc_auc_ovr'].mean()])
print(dummy_model_table)
print("#####################################################################")

# baseline0.fit(X_train,y_train)
# dummy_pred = baseline0.predict(X_train)
# Cmatrix_and_percentages(y_train,dummy_pred,"Modelo base")
