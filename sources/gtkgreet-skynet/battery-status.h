/* Read-only battery label shared by the SKYNET greeter and lock decoration. */
#ifndef BATTERY_STATUS_H
#define BATTERY_STATUS_H
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef BATTERY_ROOT
#define BATTERY_ROOT "/sys/class/power_supply"
#endif

static int battery_read(const char *path,char *out,size_t size) {
  if (!size) return 0;
  out[0]='\0';
  FILE *file=fopen(path,"re");
  if (!file) return 0;
  int ok=fgets(out,(int)size,file)!=NULL;
  fclose(file);
  if (!ok) return 0;
  out[strcspn(out,"\r\n")]='\0';
  return out[0]!='\0';
}

/* This laptop exposes its internal battery as BAT0 and AC supply as ADP1.
 * The wireless mouse battery is intentionally excluded. Read fresh on each
 * update. AC online is authoritative if the battery status temporarily lags. */
static int battery_label(char *label,size_t size) {
  char text[64],status[64];
  if (!size) return -1;
  label[0]='\0';
  if (!battery_read(BATTERY_ROOT "/BAT0/present",text,sizeof(text)) ||
      strcmp(text,"1") ||
      !battery_read(BATTERY_ROOT "/BAT0/capacity",text,sizeof(text)) ||
      strspn(text,"0123456789")!=strlen(text)) return -1;
  errno=0;char *end;
  long percent=strtol(text,&end,10);
  if (errno || *end || percent<0 || percent>100) return -1;
  battery_read(BATTERY_ROOT "/BAT0/status",status,sizeof(status));
  int online=-1;
  if (battery_read(BATTERY_ROOT "/ADP1/online",text,sizeof(text))) {
    if (!strcmp(text,"0")) online=0;
    else if (!strcmp(text,"1")) online=1;
  }
  const char *state="";
  if (online==0) state=" · On battery";
  else if (online==1) {
    if (!strcmp(status,"Charging")) state=" · Charging";
    else if (!strcmp(status,"Full")) state=" · Full · Plugged in";
    else state=" · Plugged in";
  } else {
    if (!strcmp(status,"Charging")) state=" · Charging";
    else if (!strcmp(status,"Full")) state=" · Full";
    else if (!strcmp(status,"Discharging")) state=" · On battery";
  }
  snprintf(label,size,"Battery: %ld%%%s",percent,state);
  return (int)percent;
}
#endif
