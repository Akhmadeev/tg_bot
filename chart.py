import matplotlib.pyplot as plt

def save_chart(symbol, closes):
    plt.figure(figsize=(8, 4))
    plt.plot(closes[-50:], label="Цена")
    plt.title(f"{symbol} - График")
    plt.xlabel("Время")
    plt.ylabel("Цена")
    plt.grid(True)
    path = f"{symbol}.png"
    plt.savefig(path)
    plt.close()
    return path