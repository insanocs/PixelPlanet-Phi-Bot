import os
from configparser import ConfigParser

import disnake
from disnake import TextChannel
from disnake.ext import commands
import shutil
import time

#merda ipnicial
print(f"[CONSOLE] Starting.")
print(f"[CONSOLE] List of factions: not enabled")
#configuraçoes

config = ConfigParser()
config.read(r'config.ini')
try:
  token = os.environ['TOKEN']
  print('TOKEN found in environment secrets')
except KeyError:
  token = config['BOTCONFIG']['token']
  if len(token) <= 10:
    print(f'[ERROR] IMPROPER TOKEN, CONFIGURE IT IN CONFIG.INI')
  else:
    print(f'[CONSOLE] TOKEN has been found ')
  
except Exception as e:
  print(f'TOKEN could not be found anywhere. ERROR: {e}')

try:
  bot_name = config['BOTCONFIG']['name']
  auth_id = config['BOTCONFIG']['auth_id']
  prefix = config['BOTCONFIG']['prefix']
except:
  print('Error parsing config file')
  exit()
#config do bote
#disnake presence. se o bot for banido por causa de erros, mudar isso pra uma task async

class MyClient(disnake.ext.commands.InteractionBot):

    async def on_ready(self):
        print('-'*10)
        print(f'[CONSOLE] Bot started as {self.user}. ID: {self.user.id}. Latency: {self.latency}. Prefix: "{prefix}"')
        print('-'*10)
        guilds = [guild.id for guild in self.guilds]
        #server_ids = [int(pathFaction.split("_")[0]) for pathFaction in os.listdir("./factions/")]
        #print(f"SERVER IDS: {server_ids}, GUILDS: {guilds}")
        #not_setup = 0
        #or guild_id in guilds:
        #  if guild_id not in server_ids:
        #    server = disnake.utils.get(self.guilds, id=guild_id)
        #    await server.leave()
        #    time.sleep(0.5)
        #print(f"NOT SETUP: {not_setup}")
        await self.change_presence(status=disnake.Status.online, activity=disnake.Game(name=f'->in {len(guilds)}/100 guilds<-'))
        #await self.change_presence(status=disnake.Status.online, activity=disnake.Game(name=f"We're back: -GIVE THE BOT 'Application commands' permissions. TYPE /setup (faction_name) BEFORE USING THE BOT"))

    #async def on_message(self, message):
        #if message.content.startswith("g!"):
        #    await message.add_reaction('🤔')
        #if ' phi ' in message.content.lower() or ' phi' in message.content.lower() or 'phi ' in message.content.lower() or 'phi' == message.content.lower():
        #    await message.add_reaction('🤔')
        #if message.author.bot:
        #    return
    async def on_guild_remove(self, guild):
        print("[CONSOLE] Kicked from guild '{0.name}' (ID: {0.id})".format(guild))

    async def on_guild_join(self, guild):
        #Configuração inicial pra cada server. Neccessário que rodem o comando de configuração
        print(f"[CONSOLE] Joined new guild '{guild.name}' (ID: {guild.id})")
        newpath = f'./factions/{guild.id}' 
        prefixed = [filename for filename in os.listdir('./factions/') if filename.startswith(f"{guild.id}")]
        if len(prefixed) == 0:
            if not os.path.exists(newpath):
                os.makedirs(newpath)
                shutil.copy('_phi_-418_-21_e_.png', newpath)
        await print_welcome_message(guild)

intents = disnake.Intents.default()
intents.members = False
intents.message_content = False
client = MyClient(intents=intents)

print('[CONSOLE] All cogs loaded.')

async def print_welcome_message(guild):
    #yes this is straight from starlight glimmer
    """Print a welcome message when joining a new server."""
    channels = (x for x in guild.channels if x.permissions_for(guild.me).send_messages and type(x) is TextChannel)
    c = next((x for x in channels if x.name == "general"), next(channels, None))
    if c:
        await c.send(f"I'm {bot_name}. If you need any help: discord.io/phibot or @nisano#2763. "
                     "Supporting only PixelPlanet. Hosted on Square Cloud")
        print("[CONSOLE] Printed welcome message")
    else:
        print("[CONSOLE] Could not print welcome message: no default channel found")

initial_extensions = [("cogs." + filename[:-3]) for filename in os.listdir('./cogs')]
for extension in initial_extensions:
    if extension.startswith('cogs.__pycach'):
        pass
    else:
        client.load_extension(extension)

try:
    if len(token) <= 10:
      raise Exception
    else:
      client.run(token)
except Exception as e:
    print(f"Error e: {e}, killing container")
    os.system("kill 1")