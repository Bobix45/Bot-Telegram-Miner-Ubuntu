# -*- coding: utf-8 -*-
import os
import logging
import subprocess
from datetime import datetime
import asyncio
import json
import getpass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# CONFIG
with open("/home/user/config.json", "r") as f:
    config = json.load(f)
TOKEN = config["TOKEN"]
CHAT_ID = config["CHAT_ID"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Récupérer le nom d'hôte (nom de la machine)
HOSTNAME = subprocess.getoutput("hostname")

def get_temperatures():
    cpu_temp_raw = subprocess.getoutput("sensors | grep -E 'Tctl|Tdie|Package id 0' | awk '{print $2}' | tr -d '+' | tr -d '°C'")
    gpu_temp_raw = subprocess.getoutput("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits")

    cpu_temp = int(float(cpu_temp_raw)) if cpu_temp_raw.replace('.', '', 1).isdigit() else 0
    gpu_temp = int(float(gpu_temp_raw)) if gpu_temp_raw.replace('.', '', 1).isdigit() else 0

    return cpu_temp, gpu_temp

# START BOT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔄 Redémarrer", callback_data="reboot"),
            InlineKeyboardButton("🌡️ Température", callback_data="temp"),
            InlineKeyboardButton("🖼️ NVIDIA-SMI", callback_data="nvidia_smi"),
        ],
        [
            InlineKeyboardButton("📒 Logs Miner", callback_data="logs"),
            InlineKeyboardButton("📶 Connexion", callback_data="ping"),
            InlineKeyboardButton("🌐 IP Machine", callback_data="ip_info"),
        ],
        [
            InlineKeyboardButton("🖥️ screen -r", callback_data="screen"),
            InlineKeyboardButton("🛑 Kill un Screen", callback_data="close_screen"),
            InlineKeyboardButton("✅ État", callback_data="status"),
        ],
        [
            InlineKeyboardButton("🧑‍💻 Terminal", callback_data="shell"),
        ],
        [
            InlineKeyboardButton("📊 CPU %", callback_data="cpu"),
            InlineKeyboardButton("📈 GPU %", callback_data="gpu"),
            InlineKeyboardButton("📈 RAM", callback_data="ram"),
        ],
        [
            InlineKeyboardButton("⚡ Régler PL", callback_data="ask_pl"),
            InlineKeyboardButton("🎯 OC GPU 3000", callback_data="oc_gpu_menu"),
            InlineKeyboardButton("🌀 Régler Fan GPU", callback_data="set_fan"),
        ],
        [
            InlineKeyboardButton("💽 Espace Disque", callback_data="disk"),
        ],
        [
            InlineKeyboardButton("▶️ Démarrer Service", callback_data="start_service"),
            InlineKeyboardButton("⛔ Arrêter Service", callback_data="stop_service"),
        ],  
        [ 
            InlineKeyboardButton("🧠 Coins CPU", url="https://www.hashrate.no/cpus"),
            InlineKeyboardButton("🎨 Coins GPU", url="https://www.hashrate.no/gpus"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Que veux-tu faire ?", reply_markup=reply_markup)

async def monitor_temperature():
    bot = Bot(token=TOKEN)
    while True:
        try:
            cpu_temp, gpu_temp = get_temperatures()
            print(f"[Temp Monitor] CPU: {cpu_temp}°C | GPU: {gpu_temp}°C")

            if cpu_temp > 90:
                await bot.send_message(chat_id=CHAT_ID, text=f"🚨 ALERTE : Température CPU élevée : {cpu_temp}°C")
            if gpu_temp > 90:
                await bot.send_message(chat_id=CHAT_ID, text=f"🚨 ALERTE : Température GPU élevée : {gpu_temp}°C")

        except Exception as e:
            print(f"Erreur surveillance température : {e}")

        await asyncio.sleep(180)

# BOUTONS

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "reboot":
        await query.edit_message_text("Redémarrage en cours...")
        os.system("sudo reboot")

    elif action == "temp":
        cpu_temp = subprocess.getoutput("sensors")
        gpu_temp = subprocess.getoutput("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits")
        await query.edit_message_text(f"🌡️ Températures\n\nCPU:\n{cpu_temp}\n\nGPU: {gpu_temp.strip()}°C")

    elif action == "nvidia_smi":
        await query.edit_message_text("📋 Lecture de l'état NVIDIA-SMI en cours...")
        smi_output = subprocess.getoutput("nvidia-smi")
        oc_output = subprocess.getoutput("py-nvtool")

        # Envoie d'abord NVIDIA-SMI
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"```\n=== NVIDIA-SMI ===\n{smi_output}\n```",
            parse_mode="Markdown"
        )

        # Ensuite py-nvtool
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"```\n=== Overclock (py-nvtool) ===\n{oc_output}\n```",
            parse_mode="Markdown"
        )

    elif action == "logs":
        await query.edit_message_text("📒 Recherche des sessions screen actives...")

        # Récupère sessions user
        user_screens = subprocess.getoutput("screen -ls | grep Detached | awk '{print $1}'").splitlines()
        # Récupère sessions root
        root_screens = subprocess.getoutput("sudo screen -ls | grep Detached | awk '{print $1}'").splitlines()

        if not user_screens and not root_screens:
            await context.bot.send_message(chat_id=CHAT_ID, text="⚠️ Aucun screen détaché trouvé.")
        else:
            buttons = []

            for sid in user_screens:
                buttons.append([InlineKeyboardButton(f"👤 Voir log USER {sid}", callback_data=f"viewlog_user_{sid}")])

            for sid in root_screens:
                buttons.append([InlineKeyboardButton(f"🛡️ Voir log ROOT {sid}", callback_data=f"viewlog_root_{sid}")])

            reply_markup = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(chat_id=CHAT_ID, text="📒 Choisis une session pour voir ses logs :", reply_markup=reply_markup)

    elif action.startswith("viewlog_"):
        parts = action.split("_", 2)
        mode = parts[1]  # 'user' ou 'root'
        sid = parts[2]
        temp_log = f"/tmp/screenlog_{sid}.txt"

        if mode == "root":
            cmd = f"sudo screen -S {sid} -X hardcopy {temp_log}"
        else:
            cmd = f"screen -S {sid} -X hardcopy {temp_log}"

        subprocess.run(cmd, shell=True)

        if os.path.exists(temp_log):
            log_output = subprocess.getoutput(f"tail -n 50 {temp_log}")
            await context.bot.send_message(chat_id=CHAT_ID, text=f"📄 Logs `{sid}` ({mode}) :\n```\n{log_output}\n```", parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"❌ Aucun log trouvé pour la session `{sid}` en mode `{mode}`.")

    elif action == "ping":
        await query.edit_message_text("📶 Test de la connexion en cours...")

        # Test du ping rapide
        ping_result = subprocess.getoutput("ping -c 4 8.8.8.8")
    
        # Vérification installation speedtest
        if not os.path.exists("/snap/bin/speedtest"):
            await context.bot.send_message(chat_id=CHAT_ID, text="⚙️ Speedtest non trouvé. Tentative d'installation...")
            install_result = subprocess.getoutput("sudo snap install speedtest")
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚙️ Résultat installation :\n\n{install_result}")

            if not os.path.exists("/snap/bin/speedtest"):
                await context.bot.send_message(chat_id=CHAT_ID, text="❌ Échec de l'installation de Speedtest. Abandon.")
                await context.bot.send_message(chat_id=CHAT_ID, text="💡 Merci d'installer manuellement sur la machine speedtest avec :\n\n`sudo snap install speedtest`", parse_mode="Markdown")
                return

        # Accepter licence Speedtest
        subprocess.getoutput("/snap/bin/speedtest --accept-license --accept-gdpr --format=json")

        await context.bot.send_message(chat_id=CHAT_ID, text="🚀 Speedtest en cours...")

        # Lance Speedtest en JSON
        raw_result = subprocess.getoutput("/snap/bin/speedtest --format=json")

        try:
            speedtest_data = json.loads(raw_result)
            ping_speedtest = speedtest_data["ping"]["latency"]
            download = speedtest_data["download"]["bandwidth"] * 8 / 1_000_000  # Mbps
            upload = speedtest_data["upload"]["bandwidth"] * 8 / 1_000_000      # Mbps

            final_message = (
                "📶 **Résultats de la connexion :**\n\n"
                "🌍 **Ping Google 8.8.8.8 :**\n"
                f"```\n{ping_result}\n```\n"
                "🌍 **Speedtest.net :**\n"
                f"📡 Ping : `{ping_speedtest:.2f}` ms\n"
                f"📥 Download : `{download:.2f}` Mbps\n"
                f"📤 Upload : `{upload:.2f}` Mbps"
            )

            await context.bot.send_message(chat_id=CHAT_ID, text=final_message, parse_mode="Markdown")

        except Exception as e:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Erreur en lisant le Speedtest : {e}\n\n{raw_result}")

    elif action == "ip_info":
        await query.edit_message_text("🌐 Récupération des IPs...")
        ip_local = subprocess.getoutput("hostname -I | awk '{print $1}'")
        ip_public = subprocess.getoutput("curl -4 -s ifconfig.me")
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🌐 IP Locale : `{ip_local}`\n🌍 IP Publique : `{ip_public}`",
            parse_mode="Markdown"
    )

    elif action == "screen":
        await query.edit_message_text("🖥️ Recherche des sessions screen...")

        try:
            import getpass
            normal_user = getpass.getuser()

            # Sessions user
            result_user = subprocess.getoutput(f"sudo -u {normal_user} screen -ls")
            # Sessions root
            result_root = subprocess.getoutput("sudo screen -ls")

            result = "📂 Sessions utilisateur :\n" + result_user + "\n\n🛡️ Sessions root :\n" + result_root
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🖥️ Sessions screen :\n\n{result}")
        except Exception as e:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"❌ Erreur screen : {e}")

    elif action == "close_screen":
        await query.edit_message_text("🔎 Recherche des sessions screen...")

        user_screens = subprocess.getoutput("screen -ls | grep Detached | awk '{print $1}'").splitlines()
        root_screens = subprocess.getoutput("sudo screen -ls | grep Detached | awk '{print $1}'").splitlines()

        if not user_screens and not root_screens:
            await context.bot.send_message(chat_id=CHAT_ID, text="⚠️ Aucun screen détaché trouvé.")
        else:
            buttons = []
            for sid in user_screens:
                buttons.append([InlineKeyboardButton(f"👤 Fermer USER {sid}", callback_data=f"kill_user_{sid}")])
            for sid in root_screens:
                buttons.append([InlineKeyboardButton(f"🛡️ Fermer ROOT {sid}", callback_data=f"kill_root_{sid}")])
        
            reply_markup = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(chat_id=CHAT_ID, text="🛑 Choisis une session à fermer :", reply_markup=reply_markup)

    elif action.startswith("kill_"):
        parts = action.split("_", 2)
        mode = parts[1]  # user ou root
        sid = parts[2]

        if mode == "root":
            result = subprocess.run(f"sudo screen -S {sid} -X quit", shell=True)
        else:
            result = subprocess.run(f"screen -S {sid} -X quit", shell=True)

        if result.returncode == 0:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ Session `{sid}` ({mode}) fermée avec succès.")
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"❌ Impossible de fermer la session `{sid}` en mode `{mode}`.")

    elif action == "status":
        await query.edit_message_text("✅ Le bot est toujours actif.")

    elif action == "shell":
        await query.edit_message_text("💬 Envoie-moi la commande à exécuter dans le shell.")
        context.user_data["awaiting_command"] = True

    elif action == "cpu":
        await query.edit_message_text("📊 Lecture de l'utilisation CPU...")
        result = subprocess.getoutput("vmstat 1 2 | tail -1 | awk '{print 100 - $15}'")
        await context.bot.send_message(chat_id=CHAT_ID, text=f"📊 CPU utilisé : {result.strip()} %")

    elif action == "gpu":
        await query.edit_message_text("📈 Lecture de l'utilisation GPU...")
        result = subprocess.getoutput("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits")
        await context.bot.send_message(chat_id=CHAT_ID, text=f"📈 GPU utilisé : {result.strip()} %")

    elif action == "ram":
        await query.edit_message_text("📈 Lecture de l'utilisation de la RAM...")
        ram_output = subprocess.getoutput("free -m")
        lines = ram_output.splitlines()
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                total_mb = parts[1]
                used_mb = parts[2]
                free_mb = parts[6]
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=(
                        f"📦 RAM totale installée : {total_mb} Mo\n"
                        f"📈 RAM utilisée : {used_mb} Mo\n"
                        f"📗 RAM disponible : {free_mb} Mo"
                    )
                )
                break

    elif action == "ask_pl":
        await query.edit_message_text("💬 Quel Power Limit (W) veux-tu appliquer ? (ex: 150)")
        context.user_data["awaiting_pl_value"] = True

    elif action == "oc_gpu_menu":
        buttons = [
            [InlineKeyboardButton("✅ Automatique", callback_data="oc_gpu_auto")],
            [InlineKeyboardButton("⚙️ Manuel", callback_data="oc_gpu_manual")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Choisis le mode :", reply_markup=reply_markup)

    elif action == "oc_gpu_auto":
        await query.edit_message_text("🎯 Application automatique de l'OC GPU 3000...")
        cmd = "sudo py-nvtool --setclocks 1400 --setcoreoffset 200 --setmem 6800 --setmemoffset 2000 --setpl 230 --setfan 55"
        result = subprocess.getoutput(cmd)
        await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ Résultat :\n```\n{result}\n```", parse_mode="Markdown")

    elif action == "oc_gpu_manual":
        await query.edit_message_text("⚙️ Saisie manuelle des paramètres.\n\n💬 Envoie-moi `setclocks` (ex: 1400)")
        context.user_data["awaiting_nvtool"] = {
            "step": "setclocks",
            "data": {}
        }

    elif action == "set_fan":
        await query.edit_message_text("💬 Quelle vitesse de ventilateur veux-tu appliquer ? (en %, ex: 60)")
        context.user_data["awaiting_fan_speed"] = True

    elif action == "disk":
        await query.edit_message_text("💽 Lecture de l'espace disque simplifié...")
        output = subprocess.getoutput("df -h / | tail -1")
        parts = output.split()
        if len(parts) >= 5:
            total = parts[1]
            used = parts[2]
            avail = parts[3]
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"💽 Espace total : {total}\n💽 Espace utilisé : {used}\n💽 Espace disponible : {avail}"
            )
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text="❌ Erreur de lecture de l'espace disque.")

    elif action == "start_service" or action == "stop_service":
        operation = "start" if action == "start_service" else "stop"
        services = ["qubitcoin", "qubic", "tari", "tig"]
        buttons = [
            [InlineKeyboardButton(service.upper(), callback_data=f"{operation}_{service}")] for service in services
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(f"🛠️ Choisis un service à {operation} :", reply_markup=reply_markup)

    elif action.startswith("start_") or action.startswith("stop_"):
        _, service = action.split("_", 1)
        await query.edit_message_text(f"{'▶️ Démarrage' if action.startswith('start_') else '⛔ Arrêt'} de {service}...")
        cmd = f"sudo /usr/bin/systemctl {'start' if action.startswith('start_') else 'stop'} {service}"
        result = subprocess.getoutput(cmd)
        await context.bot.send_message(chat_id=CHAT_ID, text=f"✅ Commande exécutée :\n`{cmd}`", parse_mode="Markdown")

# COMMANDES TEXTE

import json

async def handle_command_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_command"):
        context.user_data["awaiting_command"] = False
        cmd = update.message.text
        await update.message.reply_text(f"⚙️ Exécution de : `{cmd}`", parse_mode="Markdown")
        output = subprocess.getoutput(cmd)
        if len(output) > 4000:
            output = output[:4000] + "\n[...]"
        await update.message.reply_text(f"📄 Résultat :\n```\n{output}\n```", parse_mode="Markdown")
    
    if context.user_data.get("awaiting_pl_value"):
        context.user_data["awaiting_pl_value"] = False
        pl_value = update.message.text.strip()
        if pl_value.isdigit():
            result = subprocess.getoutput(f"sudo nvidia-smi -pl {pl_value}")
            await update.message.reply_text(f"⚡ Power Limit réglé à {pl_value}W\n\nRésultat :\n{result}")
        else:
            await update.message.reply_text("❌ Merci de saisir un nombre valide pour le Power Limit.")
        return

    if "awaiting_nvtool" in context.user_data:
        nv_state = context.user_data["awaiting_nvtool"]
        value = update.message.text.strip()
        step = nv_state["step"]
        nv_state["data"][step] = value

        next_steps = {
            "setclocks": "setcoreoffset",
            "setcoreoffset": "setmem",
            "setmem": "setmemoffset",
            "setmemoffset": "setpl",
            "setpl": "setfan",
        }

    if step in next_steps:
        next_step = next_steps[step]
        nv_state["step"] = next_step

        examples = {
            "setcoreoffset": "200",
            "setmem": "6800",
            "setmemoffset": "2000",
            "setpl": "250",
            "setfan": "65"
        }

        await update.message.reply_text(
            f"💬 Envoie-moi `{next_step}` (ex: {examples.get(next_step, '1400')})"
        )
    else:
        data = nv_state["data"]
        cmd = (
            f"sudo py-nvtool --setclocks {data['setclocks']} "
            f"--setcoreoffset {data['setcoreoffset']} "
            f"--setmem {data['setmem']} "
            f"--setmemoffset {data['setmemoffset']} "
            f"--setpl {data['setpl']} "
            f"--setfan {data['setfan']}"
        )
        result = subprocess.getoutput(cmd)
        await update.message.reply_text(f"✅ OC GPU appliqué :\n```\n{result}\n```", parse_mode="Markdown")
        del context.user_data["awaiting_nvtool"]
    return

    if context.user_data.get("awaiting_fan_speed"):
        context.user_data["awaiting_fan_speed"] = False
        value = update.message.text.strip()
        if value.isdigit() and 0 <= int(value) <= 100:
            cmd = f"sudo py-nvtool --setfan {value}"
            result = subprocess.getoutput(cmd)
            await update.message.reply_text(
                f"✅ Ventilateur réglé à {value}%\n```\n{result}\n```",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Merci de saisir une valeur entre 0 et 100.")
        return
    
# NOTIFICATIONS

async def send_startup_message():
    bot = Bot(token=TOKEN)
    cpu_temp, gpu_temp = get_temperatures()
    await bot.send_message(chat_id=CHAT_ID, text=f"✅ Machine démarrée.\n🌡️ Températures : CPU {cpu_temp}°C | GPU {gpu_temp}°C")

async def send_alive_loop():
    bot = Bot(token=TOKEN)
    while True:
        cpu_temp, gpu_temp = get_temperatures()
        now = datetime.now().strftime("%H:%M:%S")
        try:
            await bot.send_message(chat_id=CHAT_ID, text=f"❤️ Still alive - {now}\n🌡️ CPU : {cpu_temp}°C | GPU : {gpu_temp}°C")
        except Exception as e:
            print("Erreur d'envoi heartbeat :", e)
        await asyncio.sleep(43200)

# MAIN

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_command_input))

    async def startup(app):
        await send_startup_message()
        asyncio.create_task(send_alive_loop())

    app.post_init = startup
    app.run_polling()
