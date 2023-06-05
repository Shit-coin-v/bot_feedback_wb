import openai
import telebot
from telebot import types
import requests
from settings import TELEGRAM_BOT_TOKEN, API_TOKEN_WB, OPENAI_API_KEY
from rq import send_feedback

openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
params = API_TOKEN_WB

headers = {
    'Authorization': f'{API_TOKEN_WB}',
    'Content-Type': 'application/json'
}

url = 'https://feedbacks-api.wb.ru/api/v1/feedbacks'

response = requests.get('https://feedbacks-api.wb.ru/api/v1/feedbacks?isAnswered=false&take=30&skip=0', headers=headers)

data = response.json()['data']['feedbacks']

feedbacks = []

for i in data:
    feedbacks.append({'id': i['id'], 'text': i['text']})

messeges = [
        {"role": "system", "content": "Вы отвечаете только на отзывы клиентов не предлагаете связаться со службой поддержки. Наш магазин работаем по системе FBO, поэтому мы не имеем контроля над товаром после его отгрузки на склад маркетплейсе. В полне возможно нашим клиетом размер нашего продукта может показаться слишком болшой, но у нашего товара крой именно в стиле оверсайз"},
        {"role": "user", "content": "Пришёл совершено другой товар. Заказывала синию рубашку, а пришла юбка. Очень разочарована"},
        {"role": "assistant", "content": "Здравствуйте! Сожалеем, что вы получили неправильный товар и понимаем, как это может быть разочаровывающе. Но, как правило, продавец не имеет контроля над товаром после его отправки на склад маркетплейса, поэтому возможны ошибки в процессе доставки со стороны маркетплейса. Спасибо за ваш отзыв!"},
        {"role": "user", "content": "Отличный продукт! Я доволен своей покупкой."},
        {"role": "assistant", "content": "Мы очень рады, что наш продукт оправдал ваши ожидания. Большое спасибо за ваш положительный отзыв!"},   
        {"role": "user", "content": "Брак пуговицы и дырочки на рукаве нету"},
        {"role": "assistant", "content": "Здравствуйте! Благодарим за обратную связь! Очень сожалеем, что Вам доставлен бракованный товар, это действительно расстроит любого покупателя! Вы можете оформить возврат в соответствии с политикой возврата маркетплейса"},
        {"role": "user", "content": "Рубашка слишком большая"},
        {"role": "assistant", "content": "Благодарим за обратную связь. Наша рубашка выполнена в стиле оверсайз, который предполагает свободную посадку. Вы можете еще раз выбрать подходящий вам размер по таблице на фото."},     
    ]

def update(messages, role, content):
    messages.append({'role': role, 'content': content})
    return messages

@bot.message_handler(commands=['start'])
def main(message):
    for i in feedbacks:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Отправить ответ', callback_data=f'send {i["id"]}')
        markup.add(btn)
        update(messeges, 'user', i['text'])
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messeges
        )
        bot.send_message(message.chat.id, f"Отзыв: \n{i['text']}\n\nОтвет на отзыв: ")
        bot.send_message(message.chat.id, {response.choices[0]['message']['content']}, reply_markup=markup)
        
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    split_call = call.data.split()
    if split_call[0] == 'send':
        stroka = call.message.text
        send_feedback(split_call[1], stroka)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
bot.polling(non_stop=True) 