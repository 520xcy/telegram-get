from telethon import TelegramClient, sync, errors, events, utils
from telethon.tl.types import PeerChannel, MessageMediaWebPage, PeerChat, InputPeerUser
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.functions.users import GetUsersRequest
import os 
api_id = 2442549
api_hash = 'f7344ff578d2704d2ad9ca3beb977ef1'
bot_token = '1596491120:AAG0pbXbe7l-jmZa84F6okKQSCAKUlhWFWc'
proxy = {'proxy_type': 'socks5', 'addr': '192.168.254.250', 'port': 1080}

class tg_watchon_class:
    def __init__(self, project_path):
# We have to manually call "start" if we want an explicit bot token
        self.bot = TelegramClient('bot', api_id, api_hash,proxy=proxy).start(bot_token=bot_token)
    
        @self.bot.on(events.NewMessage)
        async def handler(event):
                # print("handler init success")
                print('sender:', str(event.input_sender),' to:', str(event.message.to_id))
                print('message:', event.raw_text)
                await event.reply('你也好呀')
    def start(self):
        print('(Press Ctrl+C to stop this)')
        self.bot.run_until_disconnected()
if __name__ == '__main__':

    PROJECT_PATH = os.path.split(os.path.realpath(__file__))[0]

    t = tg_watchon_class(PROJECT_PATH)
    t.start()