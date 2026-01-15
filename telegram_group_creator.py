import asyncio
import os
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.messages import CreateChatRequest, AddChatUserRequest
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from telethon.tl.types import InputPeerUser
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class TelegramGroupCreator:
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone_number = os.getenv('PHONE_NUMBER')
        
        if self.api_id:
            try:
                self.api_id = int(self.api_id)
            except ValueError:
                raise ValueError("API_ID sayısal bir değer olmalıdır!")
        
        if not all([self.api_id, self.api_hash, self.phone_number]):
            raise ValueError("API_ID, API_HASH ve PHONE_NUMBER değerleri .env dosyasında tanımlanmalıdır!")
        
        self.client = TelegramClient(
            'session', 
            self.api_id, 
            self.api_hash,
            timeout=30
        )
    
    async def test_connection(self):
        try:
            print("Bağlantı test ediliyor...")
            me = await self.client.get_me()
            print(f"Bağlantı başarılı! Kullanıcı: {me.first_name} (@{me.username or 'username_yok'})")
            return True
        except Exception as e:
            print(f"Bağlantı testi başarısız: {e}")
            return False
    
    async def start_client(self):
        try:
            print("Telegram'a bağlanılıyor...")
            print(f"Telefon: {self.phone_number}")
            print(f"API ID: {self.api_id}")
            
            await self.client.start(phone=self.phone_number)
            
            if await self.test_connection():
                print("Telegram'a başarıyla bağlandı!")
                return True
            else:
                print("Bağlantı başarısız!")
                return False
                
        except SessionPasswordNeededError:
            print("İki faktörlü kimlik doğrulama aktif!")
            password = input("Lütfen 2FA şifrenizi girin: ")
            try:
                await self.client.sign_in(password=password)
                print("2FA doğrulaması başarılı!")
                return True
            except Exception as e:
                print(f"2FA doğrulaması başarısız: {e}")
                return False
                
        except PhoneCodeInvalidError:
            print("Telefon doğrulama kodu hatalı!")
            return False
            
        except FloodWaitError as e:
            print(f"Çok fazla istek gönderildi. {e.seconds} saniye bekleyin.")
            return False
            
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            print("Çözüm önerileri:")

            return False
    
    async def create_group(self, group_title, user_usernames=None):
        try:
            users = []
            if user_usernames:
                for username in user_usernames:
                    try:
                        user = await self.client.get_entity(username)
                        users.append(user)
                    except Exception as e:
                        print(f"Kullanıcı {username} bulunamadı: {e}")
            
            result = await self.client(CreateChatRequest(
                users=users,
                title=group_title
            ))
            
            group_info = {
                'id': result.chats[0].id,
                'title': result.chats[0].title,
                'participants_count': len(result.chats[0].participants) if hasattr(result.chats[0], 'participants') else 0
            }
            
            print(f"Grup başarıyla oluşturuldu!")
            print(f"Grup Adı: {group_info['title']}")
            print(f"Grup ID: {group_info['id']}")
            print(f"Katılımcı Sayısı: {group_info['participants_count']}")
            
            return group_info
            
        except Exception as e:
            print(f"Grup oluşturulurken hata oluştu: {e}")
            return None
    
    async def create_channel(self, channel_title, channel_description=""):
        try:
            result = await self.client(CreateChannelRequest(
                title=channel_title,
                about=channel_description,
                megagroup=False
            ))
            
            channel_info = {
                'id': result.chats[0].id,
                'title': result.chats[0].title,
                'username': getattr(result.chats[0], 'username', None)
            }
            
            print(f"Kanal başarıyla oluşturuldu!")
            print(f"Kanal Adı: {channel_info['title']}")
            print(f"Kanal ID: {channel_info['id']}")
            if channel_info['username']:
                print(f"Kullanıcı Adı: @{channel_info['username']}")
            
            return channel_info
            
        except Exception as e:
            print(f"Kanal oluşturulurken hata oluştu: {e}")
            return None
    
    async def add_user_to_group(self, group_id, username):
        try:
            user = await self.client.get_entity(username)
            await self.client(AddChatUserRequest(
                chat_id=group_id,
                user_id=user,
                fwd_limit=50
            ))
            print(f"{username} kullanıcısı gruba eklendi!")
            
        except Exception as e:
            print(f"Kullanıcı eklenirken hata oluştu: {e}")
    
    async def get_my_groups(self):
        try:
            dialogs = await self.client.get_dialogs()
            groups = []
            
            for dialog in dialogs:
                if dialog.is_group:
                    groups.append({
                        'id': dialog.id,
                        'title': dialog.title,
                        'participants_count': dialog.participants_count
                    })
            
            print(f"Toplam {len(groups)} grup bulundu:")
            for group in groups:
                print(f"  - {group['title']} (ID: {group['id']}, Üye: {group['participants_count']})")
            
            return groups
            
        except Exception as e:
            print(f"Gruplar listelenirken hata oluştu: {e}")
            return []
    
    async def close(self):
        await self.client.disconnect()
        print("Telegram bağlantısı kapatıldı!")

async def main():
    creator = TelegramGroupCreator()
    
    try:
        success = await creator.start_client()
        
        if not success:
            print("Bağlantı kurulamadı. Program sonlandırılıyor.")
            return
        
        print("\nGrup Oluşturma Ayarları")
        print("-" * 30)
        
        try:
            group_count = int(input("Kaç tane grup oluşturmak istiyorsunuz? "))
            if group_count <= 0:
                print("Grup sayısı 0'dan büyük olmalıdır!")
                return
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
            return
        
        try:
            delay_seconds = int(input("Gruplar arasında kaç saniye bekleme yapmak istiyorsunuz? "))
            if delay_seconds < 0:
                print("Bekleme süresi negatif olamaz!")
                return
        except ValueError:
            print("Lütfen geçerli bir sayı girin!")
            return
        
        print(f"\n{group_count} adet grup oluşturulacak...")
        print(f"Gruplar arası bekleme: {delay_seconds} saniye")
        
        created_groups = []
        for i in range(group_count):
            print(f"\nGrup {i+1}/{group_count} oluşturuluyor...")
            
            group_info = await creator.create_group(
                group_title=f"Test Grubu {i+1}",
                user_usernames=[]
            )
            
            if group_info:
                created_groups.append(group_info)
                print(f"Grup {i+1} başarıyla oluşturuldu!")
            else:
                print(f"Grup {i+1} oluşturulamadı!")
            
            if i < group_count - 1 and delay_seconds > 0:
                print(f"{delay_seconds} saniye bekleniyor...")
                await asyncio.sleep(delay_seconds)
        
        print(f"\nÖZET:")
        print(f"Başarıyla oluşturulan grup sayısı: {len(created_groups)}")
        print(f"Başarısız olan grup sayısı: {group_count - len(created_groups)}")
        
        if created_groups:
            print(f"\nOluşturulan Gruplar:")
            for i, group in enumerate(created_groups, 1):
                print(f"  {i}. {group['title']} (ID: {group['id']})")
        
        print("\nTüm Gruplarınız:")
        await creator.get_my_groups()
        
    except Exception as e:
        print(f"Genel hata: {e}")
        logger.error(f"Ana fonksiyon hatası: {e}")
    
    finally:
        await creator.close()

if __name__ == "__main__":
    print("Telegram Grup Oluşturucu")
    print("=" * 40)
    asyncio.run(main())
