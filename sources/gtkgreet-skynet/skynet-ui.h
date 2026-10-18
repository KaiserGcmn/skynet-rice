
#include <pwd.h>
#include "skynet-logo.h"
#include "battery-status.h"

static void skynet_power_done(GObject *object,GAsyncResult *result,gpointer data) {
    GError *error=NULL;
    gboolean ok=g_subprocess_wait_check_finish(G_SUBPROCESS(object),result,&error);
    if(!ok) {
        GtkWidget *dialog=gtk_message_dialog_new(GTK_WINDOW(data),GTK_DIALOG_MODAL,
            GTK_MESSAGE_ERROR,GTK_BUTTONS_CLOSE,"Power action could not be completed");
        gtk_message_dialog_format_secondary_text(GTK_MESSAGE_DIALOG(dialog),"%s",error?error->message:"Request was refused");
        gtk_dialog_run(GTK_DIALOG(dialog));gtk_widget_destroy(dialog);
        g_clear_error(&error);
    }
    g_object_unref(data);
}
static void skynet_power(GtkWidget *button,gpointer data) {
    const char *verb=g_object_get_data(G_OBJECT(button),"power-verb");
    GError *error=NULL;
    GSubprocess *process=g_subprocess_new(G_SUBPROCESS_FLAGS_NONE,&error,
        "/usr/bin/systemctl","--no-ask-password","--check-inhibitors=yes",verb,NULL);
    if(process) {
        g_subprocess_wait_check_async(process,NULL,skynet_power_done,g_object_ref(data));
        g_object_unref(process);
    } else {g_warning("Power action: %s",error->message);g_clear_error(&error);}
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
    gtk_widget_set_margin_start(brand,32);gtk_widget_set_margin_top(brand,24);
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay),brand);
    GtkWidget *footer=gtk_box_new(GTK_ORIENTATION_HORIZONTAL,12);
    gtk_widget_set_halign(footer,GTK_ALIGN_END);gtk_widget_set_valign(footer,GTK_ALIGN_END);
    gtk_widget_set_margin_end(footer,32);gtk_widget_set_margin_bottom(footer,24);
    gtk_overlay_add_overlay(GTK_OVERLAY(overlay),footer);
    const char *labels[]={"Reboot  [F11]","Shut down  [F12]"};
    const char *verbs[]={"reboot","poweroff"};
    const char *keys[]={"reboot-button","poweroff-button"};
    for(int i=0;i<2;++i) {
        GtkWidget *button=gtk_button_new_with_label(labels[i]);
        gtk_widget_set_name(button,"power-button");
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
