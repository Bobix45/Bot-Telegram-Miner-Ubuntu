# Bot-Telegram-Miner-Ubuntu
Bot Telegram multifonctions pour **contrôler et surveiller une machine Ubuntu** à distance.  
Interface avec boutons interactifs pour exécuter des commandes système et monitorer les performances.

## 📌 Fonctionnalités
- 🔄 **Redémarrer** la machine
- 🌡️ **Température** CPU et GPU
- 🖼️ **NVIDIA-SMI** + Overclock (py-nvtool)
- 📒 **Logs Miner** et consultation des sessions `screen`
- 📶 **Test connexion** (ping + speedtest)
- 🌐 **IP Machine** (locale et publique)
- 🖥️ **Lister ou fermer** des sessions `screen`
- ✅ **État du bot**
- 💻 **Terminal** à distance
- 📊 **CPU %**, 📈 **GPU %**, 📈 **RAM**
- ⚡ **Régler Power Limit** GPU
- 🎯 **OC GPU automatique** ou manuel
- 🌀 **Régler la vitesse du ventilateur**
- 💽 **Espace disque** disponible
- 🚀 **Démarrer / Arrêter un service**
- 🧠 Liens rapides vers **Coins CPU** et **Coins GPU**

<img width="541" height="471" alt="image" src="https://github.com/user-attachments/assets/f4fbe52f-a359-468c-9c15-4e8cea2f969b" />

# **Étape 1 : Ouvrir une conversation avec BotFather**

- **Ouvre l'application Telegram**  
- Dans la **barre de recherche**, tape **BotFather** *(c’est le bot officiel de Telegram pour créer des bots)*  
- Clique sur **BotFather** *(compte vérifié avec un badge bleu)*  
- Clique sur **Démarrer** (`/start`)  

---

## **Étape 2 : Créer un nouveau bot**

- Tape la commande :  /newbot

- **Donne un nom à ton bot** *(exemple : `7950x1`)* → Ce nom sera **visible** dans les conversations  
- **Donne un identifiant unique** à ton bot, **qui doit finir par `bot`** *(exemple : `rig7950x1_bot`)* → Ce nom d’utilisateur doit être **unique** dans Telegram  
- Une fois le bot créé, **clique sur Démarrer** pour l’activer  

---

## **Étape 3 : Récupérer le Token**

Une fois le bot créé, **BotFather** t’enverra un message contenant un **token** qui ressemble à :  
123456789:AAHgT9kQJkG1hFgS8nJz-Vd3uYygdjkfifh

## **Étape 4 : Récupérer ton Chat ID** *(identique pour tous tes bots)*

- **Ouvre Telegram**  
- Dans la barre de recherche, tape **@userinfobot** et ouvre la conversation officielle  
- Appuie sur **Start** *(ou envoie `/start`)*  
- Le bot te renverra un message contenant **tes infos**, dont **`Your ID`** → c’est **ton user ID Telegram**  

## **Installation sur la machine Ubuntu**
```
sudo apt update
sudo apt install lm-sensors -y
sudo apt install python3-pip -y
python3 -m pip install python-telegram-bot --break-system-packages
```
## **Création du script Python qui gère le bot**
```
nano telegram_bot.py
```
coller tout le code (telegram_bot.py)

## **Création d'un Json pour insérer le token et votre chat id (remplacer ce qui se trouve entre les guillemets par vos identifiants)**
```
nano /home/user/config.json
```
```
{
  "TOKEN": "le_token_du_bot_de_la_machine",
  "CHAT_ID": "votre id_chat"
}
```
## **Création d’un service systemd (pour que le bot se lance au démarrage de la machine:**
```
sudo nano /etc/systemd/system/telegram_bot.service
```
```
[Unit]
Description=Telegram Bot de contrôle
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/user/telegram_bot.py
WorkingDirectory=/home/user/
Restart=always
User=user

[Install]
WantedBy=multi-user.target
```
## **Activation du service:**
```
sudo systemctl daemon-reload
sudo systemctl enable telegram_bot.service --now
```
## **configuration sudo + gestion systemd pour ton bot Telegram**
```
sudo visudo
```
coller tout en bas
```
user ALL=(ALL) NOPASSWD: /usr/bin/nvidia-smi, /usr/bin/nvtool
user ALL=(ALL) NOPASSWD: /sbin/reboot
user ALL=(ALL) NOPASSWD: /usr/local/bin/py-nvtool
user ALL=(ALL) NOPASSWD: /usr/bin/screen
user ALL=NOPASSWD: /bin/systemctl start *, /bin/systemctl stop *, /bin/systemctl restart *
```
## **installer nvtool (pour gérer les oc)**
```
git clone https://github.com/Akisoft41/py-nvtool.git && cd py-nvtool && chmod +x py-nvtool.py && sudo cp py-nvtool.py /usr/local/bin/py-nvtool
```

