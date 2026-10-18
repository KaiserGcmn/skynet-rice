/* Add the current laptop battery to tuigreet's existing greeting at startup.
 * Authentication, sessions, terminal handling and updates remain in Debian's
 * /usr/bin/tuigreet. No background process and no password/input handling. */
#define _POSIX_C_SOURCE 200809L
#include <unistd.h>
#include "battery-status.h"

#ifndef TUIGREET_PROGRAM
#define TUIGREET_PROGRAM "/usr/bin/tuigreet"
#endif

int main(int argc, char **argv) {
  char label[128];
  char *greeting = NULL;
  if (battery_label(label, sizeof(label)) >= 0) {
    for (int i = 1; i + 1 < argc; ++i) {
      if (strcmp(argv[i], "--greeting") && strcmp(argv[i], "-g")) continue;
      size_t size = strlen(argv[i + 1]) + strlen(label) + 2;
      greeting = malloc(size);
      if (greeting) {
        snprintf(greeting, size, "%s\n%s", argv[i + 1], label);
        argv[i + 1] = greeting;
      }
      break;
    }
  }
  execv(TUIGREET_PROGRAM, argv);
  perror("Unable to start the installed tuigreet");
  free(greeting);
  return 127;
}
