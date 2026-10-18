
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <gtk/gtk.h>
#include "gtkgreet.h"
#include "config.h"

int config_update_command_selector(GtkWidget *combobox) {
    int entries=0;
    if(gtkgreet->command) {
        gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(combobox),gtkgreet->command,"DWM / X11");++entries;
    }
    GDir *dir=g_dir_open("/usr/share/xsessions",0,NULL);
    if(!dir) return entries;
    const char *file;
    while((file=g_dir_read_name(dir))) {
        if(!g_str_has_suffix(file,".desktop")) continue;
        char *path=g_build_filename("/usr/share/xsessions",file,NULL);
        GKeyFile *desktop=g_key_file_new();
        if(g_key_file_load_from_file(desktop,path,G_KEY_FILE_NONE,NULL)) {
            char *name=g_key_file_get_locale_string(desktop,"Desktop Entry","Name",NULL,NULL);
            char *exec=g_key_file_get_string(desktop,"Desktop Entry","Exec",NULL);
            if(name&&exec&&!strchr(exec,'%')) {
                char *command=g_strconcat("/usr/local/libexec/greetd/start-x ",exec,NULL);
                if(strlen(command)<128&&g_strcmp0(command,gtkgreet->command)) {
                    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(combobox),command,name);++entries;
                }
                g_free(command);
            }
            g_free(name);g_free(exec);
        }
        g_key_file_unref(desktop);g_free(path);
    }
    g_dir_close(dir);
    return entries;
}
