<!DOCTYPE html>
<html>
<head>
    <title>Septromino</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.2/p5.min.js"></script>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; background: black; }
        canvas { display: block; }
        .button {
            position: absolute; background: rgba(255, 255, 255, 0.8); border: 2px solid #000;
            border-radius: 5px; font-size: 20px; text-align: center; cursor: pointer;
        }
    </style>
</head>
<body>
<script>
    // Constants
    const WIDTH = 9, HEIGHT = 9, MAX_BOMBS = 10;
    const TILE_SIZE = 40, UI_WIDTH = 200;
    let scaleFactor = 1, canvasWidth, canvasHeight;
    const COLORS = {
        0: [0, 0, 0], 1: [255, 255, 255], 2: [255, 0, 0], 3: [0, 255, 0],
        4: [0, 0, 255], 5: [255, 255, 0], 6: [255, 0, 255], 7: [0, 255, 255],
        8: [128, 128, 128], 9: [255, 165, 0]
    };

    // Game state
    let field = Array(WIDTH).fill().map(() => Array(HEIGHT).fill(0));
    let clear = Array(WIDTH).fill().map(() => Array(HEIGHT).fill(0));
    let decrease = Array(WIDTH).fill().map(() => Array(HEIGHT).fill(0));
    let half = Array(WIDTH).fill().map(() => Array(HEIGHT).fill(0));
    let score = 0, level = 1, flevel = 0, chainmult = 0, chaintimer = 0;
    let token = null, token_x = 0, token_y = 0, next_token = null;
    let bombs = [], gameover = false, paused = false;
    let difficulty = 0, evil_nines = 0, levelspeed = 300;
    let display_msg = "", display_timer = 0;
    let falling_counter = 0, falling_speed = levelspeed;
    let leftBtn, rightBtn, upBtn, downBtn, pauseBtn, quitBtn, bombBtn, fullscreenBtn;
    let isLandscape = false;

    function setup() {
        // Adjust canvas for mobile
        canvasWidth = WIDTH * TILE_SIZE + UI_WIDTH;
        canvasHeight = HEIGHT * TILE_SIZE + 50;
        scaleFactor = min(windowWidth / canvasWidth, windowHeight / canvasHeight);
        if (windowWidth > windowHeight) {
            isLandscape = true;
            canvasWidth = windowWidth;
            canvasHeight = windowHeight;
            scaleFactor = 1;
        }
        let canvas = createCanvas(canvasWidth, canvasHeight);
        canvas.parent('body');
        textFont('monospace');
        textSize(24);
        randomSeed(millis());
        next_token = spawn_token();
        token_x = floor(WIDTH / 2);
        token_y = 0;
        set_level_speed();
        setup_buttons();
        windowResized();
    }

    function setup_buttons() {
        leftBtn = createDiv('⬅').class('button').position(10, height - 60).size(50, 50);
        rightBtn = createDiv('➡').class('button').position(70, height - 60).size(50, 50);
        upBtn = createDiv('⬆').class('button').position(width - 120, height - 60).size(50, 50);
        downBtn = createDiv('⬇').class('button').position(width - 60, height - 60).size(50, 50);
        pauseBtn = createDiv('P').class('button').position(10, 10).size(40, 40);
        quitBtn = createDiv('Q').class('button').position(60, 10).size(40, 40);
        bombBtn = createDiv('💣').class('button').position(110, 10).size(40, 40);
        fullscreenBtn = createDiv('FS').class('button').position(160, 10).size(40, 40);
        leftBtn.touchStarted(() => token && !paused && token_x > 0 && !field[token_x - 1][token_y] && token_x--);
        rightBtn.touchStarted(() => token && !paused && token_x < WIDTH - 2 && !field[token_x + 2][token_y] && token_x++);
        upBtn.touchStarted(() => token && !paused && ([token[0], token[1]] = [token[1], token[0]]));
        downBtn.touchStarted(() => token && !paused && (falling_speed = 4));
        pauseBtn.touchStarted(() => paused = !paused);
        quitBtn.touchStarted(() => gameover = true);
        bombBtn.touchStarted(() => bombs.length && bombs[0] === "*" && (bombs[0] = "9", display_message("Bomb activated", 50)));
        fullscreenBtn.touchStarted(toggleFullscreen);
    }

    function windowResized() {
        if (!isLandscape) {
            scaleFactor = min(windowWidth / (WIDTH * TILE_SIZE + UI_WIDTH), windowHeight / (HEIGHT * TILE_SIZE + 50));
            resizeCanvas((WIDTH * TILE_SIZE + UI_WIDTH) * scaleFactor, (HEIGHT * TILE_SIZE + 50) * scaleFactor);
        } else {
            resizeCanvas(windowWidth, windowHeight);
            scaleFactor = min(windowWidth / (WIDTH * TILE_SIZE + UI_WIDTH), windowHeight / (HEIGHT * TILE_SIZE + 50));
        }
    }

    function toggleFullscreen() {
        let fs = fullscreen();
        fullscreen(!fs);
        if (!fs && windowWidth > windowHeight) {
            document.documentElement.requestFullscreen();
        }
    }

    function spawn_digit() {
        let units = level % 10;
        let digit = floor(random(0, 6));
        if (random(0, 9) > (units + difficulty)) digit -= floor(random(0, 5));
        if (random(0, 6 + units + difficulty) < 1) digit = 6;
        if (evil_nines) return 9;
        return max(1, digit + 1);
    }

    function spawn_token() {
        return [spawn_digit(), spawn_digit()];
    }

    function set_level_speed() {
        levelspeed = 300 - (floor(level / 7) * 2 + (level % 7)) * 14;
        if (levelspeed < 20) levelspeed = 20;
    }

    function display_message(msg, duration) {
        display_msg = msg;
        display_timer = duration;
    }

    function check_septromino() {
        let hit = false;
        for (let y = HEIGHT - 1; y >= 0; y--) {
            for (let x = 0; x < WIDTH; x++) {
                if (x <= WIDTH - 3 && field[x][y] === 7 && field[x + 1][y] === 7 && field[x + 2][y] === 7) {
                    clear[x][y] = clear[x + 1][y] = clear[x + 2][y] = 1;
                    for (let [dx, dy] of [[-1, 0], [0, 1], [0, -1], [1, 0], [1, 1], [1, -1], [2, 1], [2, -1], [3, 0]]) {
                        if (x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT) half[x + dx][y + dy] = 1;
                    }
                    hit = true;
                }
                if (y <= HEIGHT - 3 && field[x][y] === 7 && field[x][y + 1] === 7 && field[x][y + 2] === 7) {
                    clear[x][y] = clear[x][y + 1] = clear[x][y + 2] = 1;
                    for (let [dx, dy] of [[0, -1], [1, 0], [-1, 0], [-1, 1], [1, 1], [-1, 2], [1, 2], [0, 3]]) {
                        if (x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT) half[x + dx][y + dy] = 1;
                    }
                    hit = true;
                }
                for (let c = 3; c <= 7; c++) {
                    if (x <= WIDTH - c) {
                        let total = 0;
                        for (let d = 0; d < c; d++) if (field[x + d][y] >= 1 && field[x + d][y] <= 6) total += field[x + d][y];
                        if (total === 7) {
                            for (let d = 0; d < c; d++) {
                                clear[x + d][y] = 1;
                                for (let [dx, dy] of [[d + 1, 0], [d - 1, 0], [d, 1], [d, -1]]) {
                                    if (x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT) decrease[x + dx][y + dy] = 1;
                                }
                            }
                            hit = true;
                        }
                    }
                    if (y <= HEIGHT - c) {
                        let total = 0;
                        for (let d = 0; d < c; d++) if (field[x][y + d] >= 1 && field[x][y + d] <= 6) total += field[x][y + d];
                        if (total === 7) {
                            for (let d = 0; d < c; d++) {
                                clear[x][y + d] = 1;
                                for (let [dx, dy] of [[1, d], [-1, d], [0, d + 1], [0, d - 1]]) {
                                    if (x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT) decrease[x + dx][y + dy] = 1;
                                }
                            }
                            hit = true;
                        }
                    }
                }
            }
        }
        return hit;
    }

    function destroy_pieces() {
        let any_marked = false;
        for (let blink = 0; blink < 4; blink++) {
            background(0);
            draw_board(blink % 2);
            let waitStart = millis();
            while (millis() - waitStart < 30);
        }
        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                if (clear[x][y]) {
                    score += (field[x][y] + level) * (chainmult + 1);
                    field[x][y] = 0;
                    any_marked = true;
                }
            }
        }
        if (any_marked) {
            flevel += (level < 25 ? 1 : 0) + 6 - ((level - 1) % 6);
            chainmult = min(chainmult + 1, 98);
            chaintimer = 200;
        }
        return any_marked;
    }

    function decrease_pieces() {
        let any_marked = false;
        for (let blink = 0; blink < 2; blink++) {
            background(0);
            draw_board(blink % 2);
            let waitStart = millis();
            while (millis() - waitStart < 20);
        }
        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                if (decrease[x][y] && field[x][y] > 1 && field[x][y] < 7) {
                    field[x][y]--;
                    any_marked = true;
                }
            }
        }
        return any_marked;
    }

    function halve_pieces() {
        let any_marked = false;
        for (let blink = 0; blink < 2; blink++) {
            background(0);
            draw_board(blink % 2);
            let waitStart = millis();
            while (millis() - waitStart < 20);
        }
        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                if (half[x][y] && field[x][y] > 1 && field[x][y] < 7) {
                    field[x][y] = floor((field[x][y] + 1) / 2);
                    any_marked = true;
                }
            }
        }
        return any_marked;
    }

    function clear_actions() {
        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                clear[x][y] = decrease[x][y] = half[x][y] = 0;
            }
        }
    }

    function gravity() {
        for (let y = HEIGHT - 1; y >= 0; y--) {
            for (let x = 0; x < WIDTH; x++) {
                if (field[x][y] && y < HEIGHT - 1 && field[x][y + 1] === 0) {
                    field[x][y + 1] = field[x][y];
                    field[x][y] = 0;
                }
            }
        }
    }

    function level_up() {
        if (flevel >= 100) {
            let n = max(0, 4 - floor(level / 3));
            level++;
            flevel = 0;
            chainmult = 0;
            set_level_speed();
            display_message("LEVEL UP!", 50);
            if (level % 5 === 0 && bombs.length < MAX_BOMBS) bombs.push("*");
            if (level < 20) {
                for (let y = HEIGHT - n; y < HEIGHT; y++) {
                    for (let x = 0; x < WIDTH; x++) field[x][y] = 0;
                }
            } else {
                evil_nines = 1 + floor((level - 20) / 2);
            }
        }
    }

    function play_piece() {
        if (!token) {
            if (field[floor(WIDTH / 2)][0] || field[floor(WIDTH / 2) + 1][0]) {
                gameover = true;
                return;
            }
            token = next_token;
            next_token = spawn_token();
            token_x = floor(WIDTH / 2);
            token_y = 0;
        }
    }

    function draw_board(inverse = false) {
        push();
        scale(scaleFactor);
        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                let col = clear[x][y] && inverse ? [128, 128, 128] : COLORS[field[x][y]];
                fill(col);
                rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                if (field[x][y]) {
                    fill(field[x][y] === 1 ? 0 : 255);
                    text(field[x][y], x * TILE_SIZE + 10, y * TILE_SIZE + 30);
                }
            }
        }
        if (token) {
            for (let i = 0; i < token.length; i++) {
                let col = COLORS[token[i]];
                fill(col);
                rect((token_x + i) * TILE_SIZE, token_y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                fill(token[i] === 1 ? 0 : 255);
                text(token[i], (token_x + i) * TILE_SIZE + 10, token_y * TILE_SIZE + 30);
            }
        }
        fill(255);
        text(`Score: ${score}`, WIDTH * TILE_SIZE + 10, 50);
        text(`Level: ${level}.${flevel.toString().padStart(2, '0')}`, WIDTH * TILE_SIZE + 10, 80);
        text(`Next: ${next_token[0]}${next_token[1]}`, WIDTH * TILE_SIZE + 10, 110);
        if (chainmult) text(`Chain: x${chainmult + 1}`, WIDTH * TILE_SIZE + 10, 140);
        if (bombs.length) text(`Bombs: [${bombs.join('')}]`, WIDTH * TILE_SIZE + 10, 170);
        if (display_msg) text(display_msg, WIDTH * TILE_SIZE + 10, 200);
        if (paused) text("PAUSE", WIDTH * TILE_SIZE + 10, 230);
        pop();
    }

    function draw() {
        if (windowWidth > windowHeight && !fullscreen()) toggleFullscreen();
        if (gameover) {
            background(0);
            display_message("GAME OVER", 100);
            draw_board();
            let waitStart = millis();
            while (millis() - waitStart < 2000);
            noLoop();
            return;
        }
        if (!paused) {
            if (falling_counter >= falling_speed) {
                falling_counter = 0;
                if (token && token_y < HEIGHT - 1 && !field[token_x][token_y + 1] && !field[token_x + 1][token_y + 1]) {
                    token_y++;
                } else {
                    if (token) {
                        field[token_x][token_y] = token[0];
                        field[token_x + 1][token_y] = token[1];
                        token = null;
                    }
                    falling_speed = levelspeed;
                }
            }
            falling_counter++;
            gravity();
            let hit = check_septromino();
            if (hit) {
                destroy_pieces();
                halve_pieces();
                decrease_pieces();
                clear_actions();
                level_up();
            }
            play_piece();
            if (chaintimer) {
                chaintimer--;
                if (chaintimer === 0) {
                    chainmult = max(0, chainmult - 1);
                    chaintimer = 200;
                }
            }
            if (display_timer) {
                display_timer--;
                if (display_timer === 0) display_msg = "";
            }
            if (bombs.length && bombs[0].match(/\d/)) {
                let bomb_timer = parseInt(bombs[0]) * 100;
                bomb_timer--;
                bombs[0] = (bomb_timer / 100).toString();
                if (bombs[0] === "0") {
                    display_message("BOOM!!!", 50);
                    bombs.shift();
                    if (bombs.length < MAX_BOMBS) bombs.push("");
                    for (let y = 0; y < HEIGHT; y++) {
                        for (let x = 0; x < WIDTH; x++) {
                            if (field[x][y] > 0) field[x][y] = max(0, field[x][y] - 3);
                        }
                    }
                }
            }
        }
        background(0);
        draw_board();
    }

    function keyPressed() {
        if (keyCode === 80) paused = !paused; // P
        if (keyCode === 81) gameover = true; // Q
        if (token && !paused) {
            if (keyCode === UP_ARROW) [token[0], token[1]] = [token[1], token[0]];
            if (keyCode === DOWN_ARROW) falling_speed = 4;
            if (keyCode === LEFT_ARROW && token_x > 0 && !field[token_x - 1][token_y]) token_x--;
            if (keyCode === RIGHT_ARROW && token_x < WIDTH - 2 && !field[token_x + 2][token_y]) token_x++;
        }
        if (keyCode === 32 && bombs.length && bombs[0] === "*") { // Space
            bombs[0] = "9";
            display_message("Bomb activated", 50);
        }
    }
</script>
</body>
</html>