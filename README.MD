# 📊 API Pointage ZKBioTime (FastAPI)

Cette application est une **API REST développée avec FastAPI** permettant d’exposer les données de pointage issues de **ZKBioTime** :
- employés
- pointages bruts
- pointages journaliers
- heures d’arrivée, de départ
- total d’heures travaillées (gestion des shifts de nuit)
- export des données (Excel)

L’API est sécurisée par **token** et peut être consommée par un frontend web, mobile ou un outil BI.

---

## 🚀 Fonctionnalités

### 👥 Gestion des employés
- Récupération de tous les employés
- Récupération d’un employé par ID

### ⏱ Pointages
- Pointages bruts (`iclock_transaction`)
- Pointages journaliers calculés (`att_payloadtimecard`)
- Heures d’arrivée et de départ
- Calcul du **total d’heures travaillées**
- Gestion correcte des **shifts de nuit**
- Détection des anomalies (badge manquant)

### 📄 Export
- Export des pointages journaliers en **Excel**
- Filtrage par date et employé

### 🔐 Sécurité
- Authentification simple via **API Token**
- Protection CORS configurable

---

## 🏗 Architecture

