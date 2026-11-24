
#include <pwd.h>
#include "skynet-logo.h"
#include "battery-status.h"
#include "skynet-hud.h"

/* Power buttons show the lock screen's states: STAND BY while the request
 * runs, BLOCKED for a few seconds if it was refused. One request at a time. */
static int skynet_power_action=-1;
static guint skynet_power_reset[2];
static gboolean skynet_power_clear(gpointer data) {
    int action=GPOINTER_TO_INT(data);
    skynet_hud.hud.power.status[action]=0;
    skynet_power_reset[action]=0;
    return G_SOURCE_REMOVE;
}
static void skynet_power_state(int action,int status) {
    if(skynet_power_reset[action]) {g_source_remove(skynet_power_reset[action]);skynet_power_reset[action]=0;}
    skynet_hud.hud.power.status[action]=status;
    if(status==2) skynet_power_reset[action]=g_timeout_add(4000,skynet_power_clear,GINT_TO_POINTER(action));
}
/* Test mode (SKYNET_GREETER_POWER_TEST): never runs a power command. */
static gboolean skynet_power_test_refuse(gpointer data) {
    skynet_power_state(GPOINTER_TO_INT(data),2);
    return G_SOURCE_REMOVE;
}

static void skynet_power_done(GObject *object,GAsyncResult *result,gpointer data) {
    GError *error=NULL;
    gboolean ok=g_subprocess_wait_check_finish(G_SUBPROCESS(object),result,&error);
    int action=skynet_power_action;
    skynet_power_action=-1;
    if(!ok) {
        g_warning("Power action could not be completed: %s",error?error->message:"Request was refused");
        g_clear_error(&error);
        if(action>=0) skynet_power_state(action,2);
    }
    g_object_unref(data);
}
static void skynet_power(GtkWidget *button,gpointer data) {
    int action=g_strcmp0(g_object_get_data(G_OBJECT(button),"power-verb"),"reboot")?1:0;
    if(skynet_power_action>=0||skynet_hud.hud.power.status[0]==1||skynet_hud.hud.power.status[1]==1) return;
    if(g_getenv("SKYNET_GREETER_POWER_TEST")) {
        skynet_power_state(action,1);
        g_timeout_add(1500,skynet_power_test_refuse,GINT_TO_POINTER(action));
        return;
    }
    const char *verb=g_object_get_data(G_OBJECT(button),"power-verb");
    GError *error=NULL;
    GSubprocess *process=g_subprocess_new(G_SUBPROCESS_FLAGS_NONE,&error,
        "/usr/bin/systemctl","--no-ask-password","--check-inhibitors=yes",verb,NULL);
    if(process) {
        g_subprocess_wait_check_async(process,NULL,skynet_power_done,g_object_ref(data));
        g_object_unref(process);
        skynet_power_action=action;
        skynet_power_state(action,1);
    } else {g_warning("Power action: %s",error->message);g_clear_error(&error);skynet_power_state(action,2);}
}
static gboolean skynet_keys(GtkWidget *window,GdkEventKey *event,gpointer data) {
    if(event->keyval==GDK_KEY_F11 || event->keyval==GDK_KEY_F12) {
        GtkWidget *button=g_object_get_data(G_OBJECT(window),event->keyval==GDK_KEY_F11?"reboot-button":"poweroff-button");
        gtk_button_clicked(GTK_BUTTON(button));return TRUE;
    }
    return FALSE;
}
static GtkWidget *skynet_overlay(GtkWidget *window) {
    GtkWidget *overlay=gtk_overlay_new();
    gtk_container_add(GTK_CONTAINER(window),overlay);
    g_object_set_data(G_OBJECT(window),"skynet-overlay",overlay);
    GtkWidget *brand=gtk_label_new("0x00 // CYBERDYNE SYSTEMS");
    gtk_widget_set_name(brand,"brand");
    gtk_widget_set_halign(brand,GTK_ALIGN_START);gtk_widget_set_valign(brand,GTK_ALIGN_START);
    gtk_widget_set_margin_start(brand,38);gtk_widget_set_margin_top(brand,26);
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay),brand);
    /* Same place and size as the lock screen's power panel (1400,1118 in
     * the 1920x1200 artwork: two 240x54 buttons, 12 px apart). */
    GtkWidget *footer=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,12);
    gtk_widget_set_halign(footer,GTK_ALIGN_END);gtk_widget_set_valign(footer,GTK_ALIGN_END);
    gtk_widget_set_margin_end(footer,28);gtk_widget_set_margin_bottom(footer,28);
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay),footer);
    const char *labels[]={"Reboot  [F11]","Shut down  [F12]"};
    const char *verbs[]={"reboot","poweroff"};
    const char *keys[]={"reboot-button","poweroff-button"};
    for(int i=0;i<2;++i) {
        GtkWidget *button=gtk_button_new_with_label(labels[i]);
        gtk_widget_set_name(button,"power-button");
        gtk_widget_set_size_request(button,240,54);
        g_signal_connect(button,"draw",G_CALLBACK(skynet_hud_button_draw),GINT_TO_POINTER(i));
        g_object_set_data(G_OBJECT(button),"power-verb",(gpointer)verbs[i]);
        g_object_set_data(G_OBJECT(window),keys[i],button);
        g_signal_connect(button,"clicked",G_CALLBACK(skynet_power),window);
        gtk_container_add(GTK_CONTAINER(footer),button);
    }
    g_signal_connect(window,"key-press-event",G_CALLBACK(skynet_keys),NULL);
    return overlay;
}

static void skynet_resize(GtkWidget *window,GtkAllocation *allocation,gpointer unused) {
    GtkWidget *logo=g_object_get_data(G_OBJECT(window),"skynet-logo");
    if(logo) {
        int width,height,wanted=allocation->height<900?250:340;
        gtk_widget_get_size_request(logo,&width,&height);
        if(height!=wanted) gtk_widget_set_size_request(logo,480,wanted);
    }
}
