/* Rotating SKYNET globe with a fixed emblem and wordmark, plus the scanning
 * caption. The globe is shared with the lock screen:
 * ../xsecurelock-style/skynet-globe.h. Drawing only: no media decoder,
 * files, input or authentication. */
#include <math.h>
#include "../xsecurelock-style/skynet-globe.h"

/* Layout in a 480x340 design space, scaled to the widget. */
#define SKYNET_GLOBE_D 290.0
#define SKYNET_GLOBE_CY 150.0

static SkyGlobe skynet_globe;  /* rebuilt only when the pixel size changes */

static void skynet_logo_paint(cairo_t *cr,double width,double height,double elapsed_ms) {
    double scale=fmin(width/480.,height/340.);
    cairo_save(cr);
    cairo_set_source_rgb(cr,0,0,0);
    cairo_paint(cr);
    /* The sphere is drawn in device pixels so it stays sharp at any scale. */
    int diameter=(int)lround(SKYNET_GLOBE_D*scale);
    if(skynet_globe.size==0 || lround(2*skynet_globe.radius)!=diameter)
        skyglobe_init(&skynet_globe,diameter);
    skyglobe_paint(cr,&skynet_globe,round(width/2),round(SKYNET_GLOBE_CY*scale),elapsed_ms);
    cairo_translate(cr,(width-480*scale)/2,0);
    cairo_scale(cr,scale,scale);
    /* Preserve the original left-to-right highlight without moving the text. */
    cairo_select_font_face(cr,"monospace",CAIRO_FONT_SLANT_NORMAL,CAIRO_FONT_WEIGHT_BOLD);
    cairo_set_font_size(cr,10.5);
    const char *caption="CYBERDYNE SYSTEMS CORPORATION";
    cairo_text_extents_t ext;
    cairo_text_extents(cr,caption,&ext);
    double x=240-ext.width/2-ext.x_bearing;
    double phase=fmod(elapsed_ms,3800.)/3800.;
    double sweep=50-60+phase*(380+120);
    cairo_set_source_rgb(cr,.20,.025,.04);
    cairo_move_to(cr,x,326);
    cairo_show_text(cr,caption);
    cairo_save(cr);
    cairo_rectangle(cr,sweep,311,60,20);
    cairo_clip(cr);
    cairo_set_source_rgb(cr,.94,.94,.96);
    cairo_move_to(cr,x,326);
    cairo_show_text(cr,caption);
    cairo_restore(cr);
    cairo_restore(cr);
}
static gboolean skynet_draw(GtkWidget *widget,cairo_t *cr,gpointer unused) {
    (void)unused;
    skynet_logo_paint(cr,gtk_widget_get_allocated_width(widget),
                     gtk_widget_get_allocated_height(widget),g_get_monotonic_time()/1000.);
    return FALSE;
}
/* ~30 fps in fixed time slots shared with the HUD (skynet-hud.h), so both
 * repaint in the same frame instead of alternating frames. */
#define SKYNET_FRAME_SLOT_US 33333
static gboolean skynet_tick(GtkWidget *widget,GdkFrameClock *clock,gpointer data) {
    gint64 *last=data,slot=gdk_frame_clock_get_frame_time(clock)/SKYNET_FRAME_SLOT_US;
    if(slot!=*last) {gtk_widget_queue_draw(widget);*last=slot;}
    return G_SOURCE_CONTINUE;
}
static GtkWidget *skynet_logo_widget(int height) {
    GtkWidget *area=gtk_drawing_area_new();
    gtk_widget_set_size_request(area,480,height);
    g_signal_connect(area,"draw",G_CALLBACK(skynet_draw),NULL);
    gtk_widget_add_tick_callback(area,skynet_tick,g_new0(gint64,1),g_free);
    return area;
}
