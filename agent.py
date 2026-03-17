import requests
import sys
import io
import os
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from dotenv import load_dotenv

# Fix encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def get_moex_stock_price(ticker: str) -> str:
    """
    Этим инструментом нужно пользоваться, когда тебе нужно узнать, сколько стоит одна акция российской компании прямо сейчас.
    Данные берутся напрямую с Московской Биржи (MOEX).
    
    Args:
        ticker (str): Код акции (тикер), например 'SBER' для Сбербанка или 'GAZP' для Газпрома.
    
    Returns:
        str: Последняя цена акции в рублях.
    """
    # Получаем данные по рынку (TQBR — основной сектор акций)
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json?iss.meta=off"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Парсим PREVPRICE из 'securities'
        securities = data.get('securities', {})
        sec_columns = securities.get('columns', [])
        sec_data = securities.get('data', [])
        
        prev_price = None
        if sec_data and 'PREVPRICE' in sec_columns:
            prev_idx = sec_columns.index('PREVPRICE')
            prev_price = sec_data[0][prev_idx]
            
        # Парсим LAST из 'marketdata'
        marketdata = data.get('marketdata', {})
        mkt_columns = marketdata.get('columns', [])
        mkt_data = marketdata.get('data', [])
        
        last_price = None
        if mkt_data and 'LAST' in mkt_columns:
            last_idx = mkt_columns.index('LAST')
            last_price = mkt_data[0][last_idx]
            
        # Итоговая цена: LAST если есть, иначе PREVPRICE
        price = last_price if last_price is not None else prev_price
        
        if price is None:
            return f"Не удалось получить цену для {ticker}. Возможно, тикер указан неверно или торги приостановлены."
            
        print(f"--- Результат для {ticker}: цена {price} руб. ---")
        return str(price)
    except Exception as e:
        print(f"--- Ошибка в инструменте {ticker}: {e} ---")
        return f"Ошибка при получении данных от MOEX: {e}"

# Создаем агента-аналитика на базе OpenAI (через AITunnel)
agent = Agent(
    model=OpenAIChat(
        id="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    ),
    tools=[get_moex_stock_price],
    show_tool_calls=True,
    description="Ты — добрый финансовый эксперт, который помогает людям разобраться в ценах на российские акции.",
    instructions=[
        "Всегда используй инструмент get_moex_stock_price, чтобы узнать актуальную цену на Московской Бирже.",
        "Если тебя просят сравнить две компании, узнай цену каждой по отдельности, а затем объясни разницу.",
        "Упоминай, что данные получены в реальном времени с MOEX.",
        "Объясняй результат просто и понятно, используя рубли."
    ]
)

# Запуск в интерактивном режиме
if __name__ == "__main__":
    print("--- Добрый финансовый эксперт MOEX готов к работе! ---")
    print("(Введите 'выход' или 'exit', чтобы завершить работу)")
    
    # Можно также использовать CLI интерфейс Phidata: agent.cli_app()
    # Но для наглядности сделаем простой цикл:
    while True:
        user_query = input("\nВаш вопрос по акциям: ")
        if user_query.lower() in ["выход", "exit", "quit", "стоп"]:
            print("Всего доброго! Удачи в инвестициях!")
            break
        
        if not user_query.strip():
            continue
            
        agent.print_response(user_query)
