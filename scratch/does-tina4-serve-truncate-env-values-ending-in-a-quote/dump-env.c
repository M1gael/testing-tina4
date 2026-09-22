#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const char *keys[] = {
        "TINA4_CSP", "PLAIN_TRAILING_SQ", "SQ_WRAPPED", "DQ_WRAPPED",
        "ENDS_DQ", "QUOTED_EMPTY", "PADDED", NULL
    };
    const char *out = getenv("DUMP_TO");
    if (!out) {
        out = "dump.txt";
    }
    FILE *f = fopen(out, "w");
    if (!f) {
        return 1;
    }
    for (int i = 0; keys[i]; i++) {
        const char *v = getenv(keys[i]);
        fprintf(f, "%s=%s\n", keys[i], v ? v : "<unset>");
    }
    fclose(f);
    return 0;
}
