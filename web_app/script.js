// Telegram Web App API
const tg = window.Telegram.WebApp;

// Initialize the app
tg.ready();
tg.expand();

// API base URL (change to your server)
const API_BASE = 'http://localhost:8001'; // For local testing; change to production URL

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

// Load user balance and tokens
async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE}/api/user/${userId}`);
        const data = await response.json();
        document.getElementById('balance').textContent = `Баланс: ${data.balance} 💰`;
        displayTokens(data.tokens);
    } catch (error) {
        console.error('Error loading user data:', error);
        document.getElementById('balance').textContent = 'Помилка завантаження';
    }
}

// Display tokens
function displayTokens(tokens) {
    const container = document.getElementById('myTokens');
    if (tokens.length === 0) {
        container.textContent = 'Немає токенів';
        return;
    }
    container.innerHTML = tokens.map(token => `<div class="token-item">${token.name}: ${token.amount} шт.</div>`).join('');
}

// Show help
function showHelp() {
    const helpText = `Допомога:
- Створюйте токени та торгуйте ними
- Грайте в казино
- Купуйте речі в магазині
- Дивіться топ гравців`;
    showOutput(helpText);
}

// Show top players
async function showTop() {
    // For now, simulate; integrate with API later
    const topText = `Топ гравців:
1. Player1 - 5000 💰
2. Player2 - 4000 💰`;
    showOutput(topText);
}

// Create token
function createToken() {
    const name = prompt('Введіть назву токена:');
    if (name) {
        sendToBot('create_coin', { name: name });
        showOutput('Токен створено!');
        loadUserData();
    }
}

// Buy token
function buyToken() {
    const name = document.getElementById('tokenName').value;
    const amount = document.getElementById('tokenAmount').value;
    if (name && amount) {
        sendToBot('buy', { name: name, amount: parseFloat(amount) });
        showOutput(`Куплено ${amount} ${name}`);
        loadUserData();
    }
}

// Sell token
function sellToken() {
    const name = document.getElementById('sellTokenName').value;
    const amount = document.getElementById('sellAmount').value;
    if (name && amount) {
        sendToBot('sell', { name: name, amount: parseFloat(amount) });
        showOutput(`Продано ${amount} ${name}`);
        loadUserData();
    }
}

// Play dice
function playDice() {
    const amount = document.getElementById('diceAmount').value;
    if (amount) {
        sendToBot('dice', { amount: parseFloat(amount) });
        showOutput('Граємо в кості!');
    }
}

// Play dice against bot
function playDiceBot() {
    const amount = document.getElementById('diceAmount').value;
    if (amount) {
        sendToBot('dice_bot', { amount: parseFloat(amount) });
        showOutput('Гра проти бота!');
    }
}

// Rob user
function robUser() {
    const target = prompt('Введіть username для пограбування:');
    if (target) {
        sendToBot('rob', { target: target });
        showOutput(`Спроба пограбувати ${target}`);
    }
}

// Show shop
function showShop() {
    const shopText = `Магазин:
1. VIP статус - 500 💰
2. Бустер прибутку - 300 💰
3. Захист від грабежу - 200 💰`;
    showOutput(shopText);
}

// Show output
function showOutput(text) {
    document.getElementById('output').textContent = text;
}

// Load initial data
loadUserData();