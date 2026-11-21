#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define MAX_ROUNDS 100

static int read_move(void) {
    char line[32];
    if (!fgets(line, sizeof line, stdin)) return 0;
    if (line[0] == 'a' || line[0] == 'A') return -1;
    if (line[0] == 'd' || line[0] == 'D') return 1;
    if (line[0] == 'q' || line[0] == 'Q') return 0;
    return 2;
}

int main(void) {
    int score = 0;
    int rounds = 0;
    int side = 0;

    srand((unsigned int)time(NULL));
    puts("LumberJackX - local practice mode");
    puts("A = move left, D = move right, Q = quit");
    puts("This is a standalone practice game; it does not connect to Telegram or online rooms.");

    while (rounds < MAX_ROUNDS) {
        int move;
        side = (rand() % 2) ? 1 : -1;

        printf("\nRound %d | Score: %d\n", rounds + 1, score);
        printf("A tree branch is on the %s. Choose a side (A/D): ",
               side < 0 ? "LEFT" : "RIGHT");
        fflush(stdout);

        move = read_move();
        if (move == 0) break;
        if (move == 2) {
            puts("Please enter A, D, or Q.");
            continue;
        }

        if (move == side) {
            puts("Hit! The branch blocked that side. Practice round over.");
            break;
        }

        ++score;
        ++rounds;
        puts("Good move.");
    }

    printf("\nPractice finished. Final score: %d\n", score);
    return 0;
}
