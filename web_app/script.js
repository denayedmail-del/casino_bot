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
- Грайте в казино з друзями або ботом
- Купуйте речі в магазині
- Дивіться топ гравців
- Давайте гроші іншим`;
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

// Give money
function giveMoney() {
    const amount = document.getElementById('giveAmount').value;
    const target = document.getElementById('giveTarget').value;
    if (amount && target) {
        sendAction('give', { amount: parseFloat(amount), target: target });
        showOutput(`Дано ${amount} користувачу ${target}`);
        loadUserData();
    }
}

// Create token
function createToken() {
    const name = document.getElementById('createTokenName').value;
    if (name) {
        sendAction('create_coin', { name: name });
        showOutput(`Токен ${name} створено!`);
        loadUserData();
    }
}

// Buy token
function buyToken() {
    const name = document.getElementById('tokenName').value;
    const amount = document.getElementById('tokenAmount').value;
    if (name && amount) {
        sendAction('buy', { name: name, amount: parseFloat(amount) });
        showOutput(`Куплено ${amount} ${name}`);
        loadUserData();
    }
}

// Sell token
function sellToken() {
    const name = document.getElementById('sellTokenName').value;
    const amount = document.getElementById('sellAmount').value;
    if (name && amount) {
        sendAction('sell', { name: name, amount: parseFloat(amount) });
        showOutput(`Продано ${amount} ${name}`);
        loadUserData();
    }
}

// Play dice (duel)
function playDice() {
    const amount = document.getElementById('diceAmount').value;
    const target = document.getElementById('diceTarget').value;
    if (amount && target) {
        sendAction('dice', { amount: parseFloat(amount), target: target });
        showOutput(`Запрошено ${target} на дуель в кості на ${amount}`);
    }
}

// Play dice against bot
function playDiceBot() {
    const amount = document.getElementById('diceBotAmount').value;
    if (amount) {
        sendAction('dice_bot', { amount: parseFloat(amount) });
        showOutput(`Гра проти бота на ${amount}!`);
    }
}

// Rob user
function robUser() {
    const target = document.getElementById('robTarget').value;
    if (target) {
        sendAction('rob', { target: target });
        showOutput(`Спроба пограбувати ${target}`);
    }
}

// Buy item from shop
function buyItem(item) {
    sendAction('buy_item', { item: item });
    showOutput(`Куплено ${item}!`);
    loadUserData();
}

// Send action to API
async function sendAction(action, params) {
    try {
        const response = await fetch(`${API_BASE}/api/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, action: action, params: params })
        });
        const data = await response.json();
        console.log(data.response);
    } catch (error) {
        console.error('Error sending action:', error);
    }
}

// Show output
function showOutput(text) {
    document.getElementById('output').textContent = text;
}

// Load initial data
loadUserData();