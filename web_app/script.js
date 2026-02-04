// Telegram Web App API
const tg = window.Telegram.WebApp;

// Initialize the app
tg.ready();
tg.expand();

// User data
let userId = tg.initDataUnsafe?.user?.id;
let username = tg.initDataUnsafe?.user?.username || 'unknown';

// Function to send data to bot
function sendToBot(action, data = {}) {
    const payload = {
        action: action,
        user_id: userId,
        username: username,
        ...data
    };
    tg.sendData(JSON.stringify(payload));
}

// Load user balance
async function loadBalance() {
    // In a real app, this would fetch from your backend
    // For now, simulate
    document.getElementById('balance').textContent = `Баланс: 1000 💰`;
}

// Show help
function showHelp() {
    const helpText = `Допомога:
- /give <сума> <користувач> - дати гроші
- /top - топ гравців
- /create_coin <назва> - створити токен
- /buy <назва> <сума> - купити токен
- /sell <назва> <сума> - продати токен
- /my_tokens - мої токени
- /dice <сума> - грати в кості
- /dice_bot <сума> - грати проти бота
- /rob <користувач> - пограбувати
- /shop - магазин`;
    document.getElementById('output').textContent = helpText;
}

// Show shop
function showShop() {
    const shopText = `Магазин:
1. VIP статус - 500 💰
2. Бустер прибутку - 300 💰
3. Захист від грабежу - 200 💰`;
    document.getElementById('output').textContent = shopText;
    // Add buy buttons here
}

// Show top players
function showTop() {
    // Simulate top players
    const topText = `Топ гравців:
1. Player1 - 5000 💰
2. Player2 - 4000 💰
3. Player3 - 3000 💰`;
    document.getElementById('output').textContent = topText;
}

// Show my tokens
function showMyTokens() {
    // Simulate tokens
    const tokensText = `Мої токени:
- Token1: 100 шт.
- Token2: 50 шт.`;
    document.getElementById('output').textContent = tokensText;
}

// Execute custom command
function executeCommand() {
    const command = document.getElementById('commandInput').value.trim();
    if (command.startsWith('/')) {
        sendToBot('command', { command: command });
        document.getElementById('output').textContent = `Виконую команду: ${command}`;
    } else {
        document.getElementById('output').textContent = 'Команда повинна починатися з /';
    }
}

// Load initial data
loadBalance();