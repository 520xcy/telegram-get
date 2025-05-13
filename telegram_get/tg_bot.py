#!/usr/bin/python3

from telethon import TelegramClient, sync, errors, events, utils
from telethon.tl.types import PeerChannel, MessageMediaWebPage, PeerChat, InputPeerUser
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.functions.users import GetUsersRequest
import random
import time
import os
import re
import json
import shelve
import shutil
from log import get_logger

GB = 1024 ** 3
MB = 1024 ** 2

class tg_client:

    def __init__(self, project_path):

        self.project_path = project_path
        self.data_storage_path = os.path.join(self.project_path, 'data_online')
        self.historydb = os.path.join(self.project_path, 'history.shelve.db')
        self.conf = self.get_conf()
        self.api_id = int(self.conf['api'])
        self.breakcount = int(self.conf['break'])
        self.api_hash = self.conf['api_hash']
        self.bot_token = self.conf['bot_token']
        
        
        self.myid = 0
        self.logger = get_logger('tg_client', 'ERROR')
        self.download = {}

        if not os.path.exists(self.data_storage_path):
            os.mkdir(self.data_storage_path)

        proxy = {'proxy_type': 'socks5', 'addr': self.conf['proxyhost'], 'port': int(self.conf['proxyport'])} if self.conf['proxyhost'] and self.conf['proxyport'] else {}
        
        self.client = TelegramClient(os.path.join(self.data_storage_path, 'bot_'+str(self.api_id)), self.api_id, self.api_hash, proxy=proxy).start(bot_token = self.bot_token)

        self.admin_id = (self.client.get_entity(self.conf['admin_id'])).id if isinstance(
            self.conf['admin_id'], str) else self.conf['admin_id'] if self.conf['admin_id'] else 0

        @self.client.on(events.NewMessage)
        async def handler(event):
            # print("handler init success")
            print('sender:', str(event.input_sender),' to:', str(event.message.to_id))
            print('message:', event.raw_text)
            self.logger.info(
                f'sender: {str(event.input_sender)} to: {str(event.message.to_id)} event: {str(event)}')

            from_id = event.peer_id.user_id
           
            if from_id == self.admin_id:
                if event.media is not None:
                    await self.media_download(entity_id=from_id, event=event, is_savefrom=bool(event.fwd_from))
                else:
                    await self.text_command(event)
                return
            
    async def media_download(self, entity_id, event, is_savefrom=False):
        try:
            offset = 0
            file_name = self.get_filename(event, is_savefrom)
            print(file_name)
            if file_name == False:
                return False
            file_size = file_name[1]

            _dir = os.path.join(self.data_storage_path, str(entity_id))
            if not os.path.exists(_dir):
                os.makedirs(_dir)

            file_name = os.path.join(_dir, file_name[0])

            if os.path.isfile(file_name):
                self.logger.critical(f'文件已存在:{file_name}')
                return False

            if os.path.isfile(file_name+'.download'):
                offset = os.path.getsize(file_name+'.download')

            self.logger.critical(f'Start Download File: {file_name}')
            try:
                self.download.update(
                    {file_name: {'total': file_size, 'now': offset}})
                with open(file_name+'.download', 'ab+') as fd:
                    async for chunk in self.client.iter_download(event.media, offset=offset):
                        fd.write(chunk)
                        self.download[file_name]['now'] += len(chunk)
                # await self.client.download_media(event.media, file_name)
            except Exception as e:
                # os.remove(file_name)
                self.logger.error(f'{e},{entity_id}:{file_name}')
                raise
            else:
                os.rename(file_name+'.download', file_name)
                event.replay(f'Finish Download File: {file_name}')
                self.logger.critical(f'Finish Download File: {file_name}')

            finally:
                del self.download[file_name]
        except Exception as e:
            await event.reply(str(e))
        else:
            return True

    async def text_command(self, event):
        # sender = await event.get_sender()
        # self.logger.error(f'entity.id: {entity.id}')

        raw_text = event.raw_text.strip()
        if raw_text.strip() == '你好':
            await event.reply('你也好呀')
       
        elif raw_text.strip().startswith('/reload') or raw_text.strip().startswith('/重载'):
            self.conf = self.get_conf()
            await self.init_conf()
            await event.reply(f'重载config.json')
        elif raw_text.strip().startswith('/cfg') or raw_text.strip().startswith('/配置'):
            msg = str(self.__dict__)
            strlist = self.cut_text(msg, 4095)
            for r in strlist:
                await event.reply(r)
        elif raw_text.strip().startswith('/status') or raw_text.strip().startswith('/状态'):
            msg = '当前状态\n'
            for _file in self.download:
                msg += '文件名:{}\n总大小:{:6.2f} MB 已下载:{:6.2f} MB\n'.format(
                    _file,
                    self.download[_file]['total']/MB,
                    self.download[_file]['now']/MB
                )
            strlist = self.cut_text(msg, 4095)
            for r in strlist:
                await event.reply(r)
        elif raw_text.strip().startswith('/space') or raw_text.strip().startswith('/空间'):

            if os.name == 'nt':
                _dir = os.path.split(os.path.realpath(__file__))[0]
                _dir = _dir.split(os.sep)

                _dir = _dir[0]+':\\'

                total_b, used_b, free_b = shutil.disk_usage(_dir)
                msg = '总磁盘空间: {:6.2f} GB\n已使用: {:6.2f} GB\n未使用  {:6.2f} GB\n'.format(
                    total_b/GB, used_b/GB, free_b/GB)

            else:
                msg = ''
                result = []
                f = os.popen('mount')
                text = f.readlines()
                f.close()
                for line in text:
                    if re.search(r'\bext\d', line):
                        result.append(line.split()[2])
                for _path in result:
                    sv = os.statvfs(_path)
                    free_b = (sv.f_bavail * sv.f_frsize)
                    total_b = (sv.f_blocks * sv.f_frsize)
                    used_b = (sv.f_blocks - sv.f_bfree) * sv.f_frsize
                    msg += '{}\n总磁盘空间: {:6.2f} GB\n已使用: {:6.2f} GB\n未使用  {:6.2f} GB\n\n'.format(
                        _path, total_b/GB, used_b/GB, free_b/GB)

            await event.reply(msg)

        else:
            await event.reply(str(event))

    async def init_conf(self):
        
        self.admin_id = (await self.client.get_entity(self.conf['admin_id'])).id if isinstance(
            self.conf['admin_id'], str) else self.conf['admin_id'] if self.conf['admin_id'] else 0

    def get_filename(self, event, is_savefrom=False):
        file_name = ''
        file_size = 0
        if type(event.media) == MessageMediaWebPage:
            return False
        if event.document:
            try:
                if event.media.document.mime_type == "image/webp":
                    file_name = f'{event.media.document.id}.webp'
                if event.media.document.mime_type == "application/x-tgsticker":
                    file_name = f'{event.media.document.id}.tgs'
                for i in event.document.attributes:
                    try:
                        file_name = i.file_name
                    except:
                        continue
            except:
                print(event.media)

        if event.photo:
            file_name = f'{event.photo.id}.jpg'
            # file_size = max(event.photo.sizes[-1]
        else:
            file_size = event.media.document.size

        if file_name == '':
            file_name = self.get_random_file_name()
            _extension = str(event.media.document.mime_type)
            _extension = _extension.split('/')[-1]
            file_name = f'{file_name}.{_extension}'

        if not event.raw_text == '':
            file_name = str(event.raw_text).replace(
                '\n', ' ') + ' ' + file_name

        _file_name, _extension = os.path.splitext(file_name)
        event_id = event.fwd_from.saved_from_msg_id if is_savefrom else event.id
    
        file_name = f'{self.format_filename(_file_name)}{_extension}'
        

        return (file_name, file_size, event_id)

    def str_find(self, s: str, t: str):
        return s.find(t) >= 0

    def get_conf(self):
        conf = {
            'api':os.getenv('API'),
            'api_hash':os.getenv('API_HASH'),
            'bot_token':os.getenv('bot_token'),
            'proxyhost':os.getenv('PROXYHOST'),
            'proxyport':os.getenv('PROXYPORT'),
            'break':os.getenv('BREAK',100),
            'watchchannel':os.getenv('WATCH_CHANNEL','').split(',') if os.getenv('WATCH_CHANNEL','') else [],
            'watchuser':os.getenv('WATCH_USER','').split(',') if os.getenv('WATCH_USER','') else [],
            'filename_black':os.getenv('FILENAME_BLACK','').split(',') if os.getenv('FILENAME_BLACK','') else [],
            'history':[_his.split('|') for _his in os.getenv('HISTORY','').split(',')] if os.getenv('HISTORY','') else [],
            'error_notice':os.getenv('ERROR_NOTICE'),
            'forward_channel':os.getenv('FORWARD_CHANNEL'),
            'admin_id':os.getenv('ADMIN_ID')
        }

        if not os.path.exists(os.path.join(self.data_storage_path, 'conf.json')):
            shutil.copy(os.path.join(self.project_path, 'conf.json'), os.path.join(self.data_storage_path, 'conf.json'))

        with open(os.path.join(self.data_storage_path, 'conf.json'), 'r', encoding='UTF-8') as r:
                conf = json.loads(r.read())   
     
        return conf

    def get_client(self):
        return self.client

    def start(self):
        print('(Press Ctrl+C to stop this)')
        self.client.run_until_disconnected()

    def format_filename(self, f):
        f = re.sub(
            u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", f)
        try:
            while len(f.encode('utf-8')) > 210:
                f = f[0:-1]
        except:
            pass
        return f

    def get_random_file_name(self):
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(22):
            salt += random.choice(H)
        t_dir = time.strftime("%Y-%m-%d", time.localtime())
        return salt

    def cut_text(self, text, lenth):
        textArr = re.findall('.{'+str(lenth)+'}', text)
        textArr.append(text[(len(textArr)*lenth):])
        return textArr




