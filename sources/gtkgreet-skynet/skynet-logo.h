/* SKYNET visual renderer, adapted from the installed lock screen. */
#include <math.h>
typedef struct { double x, y, z; } LogoVec;
typedef struct {
  LogoVec points[4], normal;
  double depth, light;
  int plate, surface; /* surface: +1 front, -1 back, 0 rim */
} LogoFace;
static const LogoVec logo_plates[3][4] = {
  {{0,-104,0}, {62,-38,0}, {0,24,0}, {-62,-38,0}},
  {{-74,-32,0}, {-9,32,0}, {-9,102,0}, {-190,102,0}},
  {{74,-32,0}, {190,102,0}, {9,102,0}, {9,32,0}}
};

static LogoVec logo_rotate(LogoVec p, double angle) {
  double c = cos(angle), s = sin(angle);
  double pitch = 0.055 * c;
  LogoVec v = {p.x*c + p.z*s, p.y, -p.x*s + p.z*c};
  return (LogoVec){v.x, v.y*cos(pitch) - v.z*sin(pitch),
                   v.y*sin(pitch) + v.z*cos(pitch)};
}

static void logo_add_face(LogoFace *faces, int *count, const LogoVec *points,
                          int plate, int surface, double angle) {
  LogoFace face = {.plate=plate, .surface=surface};
  LogoVec center = {0};
  for (int i=0; i<4; ++i) {
    face.points[i] = logo_rotate(points[i], angle);
    center.x += face.points[i].x/4; center.y += face.points[i].y/4;
    center.z += face.points[i].z/4;
  }
  LogoVec a = {face.points[1].x-face.points[0].x,
               face.points[1].y-face.points[0].y,
               face.points[1].z-face.points[0].z};
  LogoVec b = {face.points[2].x-face.points[0].x,
               face.points[2].y-face.points[0].y,
               face.points[2].z-face.points[0].z};
  LogoVec n = {a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x};
  double length = sqrt(n.x*n.x+n.y*n.y+n.z*n.z);
  if (length <= 0) return;
  n.x /= length; n.y /= length; n.z /= length;
  /* Backface culling against a perspective camera at z=1200. */
  if (-n.x*center.x - n.y*center.y + n.z*(1200-center.z) <= 0) return;
  face.normal = n; face.depth = center.z;
  face.light = fmax(0, (-0.35*n.x-0.55*n.y+0.85*n.z)/1.071214);
  faces[(*count)++] = face;
}

static const unsigned char word_dots[][2] = {{1,1},{1,2},{1,3},{2,0},{2,1},{2,2},{3,0},{3,1},{3,2},{2,3},{3,3},{4,0},{4,1},{4,2},{5,0},{5,1},{5,2},{6,0},{6,1},{6,2},{7,0},{7,1},{7,2},{8,0},{8,1},{8,2},{9,0},{9,1},{9,2},{10,0},{10,1},{10,2},{11,0},{11,1},{11,2},{12,0},{12,1},{12,2},{13,0},{13,1},{13,2},{17,0},{17,1},{17,2},{17,3},{18,0},{18,1},{18,2},{19,0},{19,1},{19,2},{18,3},{19,3},{21,3},{23,2},{22,3},{23,3},{24,1},{24,2},{25,0},{25,1},{25,2},{24,3},{25,3},{26,0},{26,1},{26,2},{27,0},{27,1},{28,0},{28,1},{29,0},{33,0},{33,1},{33,2},{33,3},{34,0},{34,1},{34,2},{35,0},{35,1},{35,2},{34,3},{35,3},{44,0},{44,1},{44,2},{45,0},{45,1},{45,2},{44,3},{45,3},{46,0},{46,1},{46,2},{46,3},{49,1},{49,2},{49,3},{50,0},{50,1},{50,2},{51,0},{51,1},{51,2},{50,3},{51,3},{52,0},{52,1},{52,2},{53,1},{53,2},{52,3},{53,3},{54,2},{54,3},{55,3},{60,0},{60,1},{60,2},{61,0},{61,1},{61,2},{60,3},{61,3},{62,0},{62,1},{62,2},{62,3},{65,2},{65,3},{66,1},{66,2},{67,0},{67,1},{67,2},{66,3},{67,3},{68,0},{68,1},{68,2},{69,0},{69,1},{69,2},{70,0},{70,1},{70,2},{71,0},{71,1},{71,2},{72,0},{72,1},{72,2},{73,0},{73,1},{73,2},{74,0},{74,1},{74,2},{75,0},{75,1},{75,2},{76,0},{76,1},{76,2},{77,0},{77,1},{77,2},{78,0},{78,1},{78,2},{81,0},{81,1},{81,2},{82,0},{82,1},{82,2},{83,0},{83,1},{83,2},{84,0},{84,1},{84,2},{85,0},{85,1},{85,2},{86,0},{86,1},{86,2},{87,0},{87,1},{87,2},{87,3},{88,0},{88,1},{88,2},{89,0},{89,1},{89,2},{88,3},{90,0},{90,1},{90,2},{91,0},{91,1},{91,2},{92,0},{92,1},{92,2},{93,0},{93,1},{93,2},{94,0},{94,1},{94,2},{1,4},{1,5},{2,4},{2,5},{2,6},{3,4},{3,5},{3,6},{4,5},{4,6},{5,5},{5,6},{4,7},{5,7},{6,5},{6,6},{7,5},{7,6},{6,7},{7,7},{8,5},{8,6},{9,5},{9,6},{8,7},{9,7},{10,5},{10,6},{11,5},{11,6},{10,7},{11,7},{12,5},{12,6},{13,5},{13,6},{12,7},{13,7},{14,6},{14,7},{17,4},{17,5},{17,6},{17,7},{18,4},{18,5},{18,6},{19,4},{19,5},{19,6},{18,7},{19,7},{20,4},{20,5},{20,6},{21,4},{21,5},{21,6},{20,7},{21,7},{22,4},{22,5},{22,6},{23,4},{22,7},{23,7},{24,4},{24,7},{33,4},{34,4},{34,5},{34,6},{35,4},{35,5},{35,6},{36,4},{36,5},{36,6},{37,4},{37,5},{37,6},{38,4},{38,5},{38,6},{39,4},{39,5},{39,6},{40,4},{40,5},{40,6},{41,4},{41,5},{41,6},{42,4},{42,5},{42,6},{43,4},{43,5},{43,6},{44,4},{44,5},{44,6},{45,4},{45,5},{45,6},{44,7},{45,7},{46,4},{46,5},{46,6},{46,7},{49,4},{49,5},{49,6},{49,7},{50,4},{50,5},{50,6},{51,4},{51,5},{51,6},{50,7},{51,7},{53,4},{54,4},{54,5},{55,4},{55,5},{55,6},{55,7},{56,4},{56,5},{56,6},{57,6},{56,7},{57,7},{58,7},{60,4},{60,5},{60,6},{61,4},{61,5},{61,6},{60,7},{61,7},{62,4},{62,5},{62,6},{62,7},{65,4},{65,5},{65,6},{65,7},{66,4},{66,5},{66,6},{67,4},{67,5},{67,6},{66,7},{67,7},{68,5},{68,6},{69,5},{69,6},{68,7},{69,7},{70,5},{70,6},{71,5},{71,6},{70,7},{71,7},{72,5},{72,6},{73,5},{73,6},{72,7},{73,7},{74,5},{74,6},{75,5},{75,6},{74,7},{75,7},{76,5},{76,6},{77,5},{77,6},{76,7},{77,7},{78,5},{78,6},{78,7},{87,4},{87,5},{87,6},{87,7},{88,4},{88,5},{88,6},{88,7},{2,9},{2,10},{3,9},{3,10},{2,11},{3,11},{4,9},{4,10},{5,9},{5,10},{4,11},{5,11},{6,9},{6,10},{7,9},{7,10},{6,11},{7,11},{8,9},{8,10},{9,9},{9,10},{8,11},{9,11},{10,9},{10,10},{11,9},{11,10},{10,11},{11,11},{12,8},{12,9},{12,10},{13,8},{13,9},{13,10},{12,11},{13,11},{14,8},{14,9},{14,10},{17,8},{17,9},{17,10},{17,11},{18,8},{18,9},{18,10},{19,8},{19,9},{19,10},{18,11},{19,11},{21,8},{22,8},{22,9},{23,8},{23,9},{24,8},{24,9},{24,10},{25,8},{25,9},{25,10},{25,11},{26,9},{26,10},{27,10},{26,11},{27,11},{28,10},{28,11},{29,11},{36,9},{36,10},{37,9},{37,10},{36,11},{37,11},{38,9},{38,10},{39,9},{39,10},{38,11},{39,11},{40,9},{40,10},{41,9},{41,10},{40,11},{41,11},{42,9},{42,10},{43,9},{43,10},{42,11},{43,11},{44,8},{44,9},{44,10},{45,8},{45,9},{45,10},{44,11},{46,8},{46,9},{49,8},{49,9},{49,10},{49,11},{50,8},{50,9},{50,10},{51,8},{51,9},{51,10},{50,11},{51,11},{56,8},{57,8},{57,9},{58,8},{58,9},{58,10},{59,8},{59,9},{59,10},{59,11},{60,8},{60,9},{60,10},{61,8},{61,9},{61,10},{60,11},{61,11},{62,8},{62,9},{65,8},{65,9},{66,8},{66,9},{66,10},{67,8},{67,9},{67,10},{67,11},{68,9},{68,10},{69,9},{69,10},{68,11},{69,11},{70,9},{70,10},{71,9},{71,10},{70,11},{71,11},{72,9},{72,10},{73,9},{73,10},{72,11},{73,11},{74,9},{74,10},{75,9},{75,10},{74,11},{75,11},{76,9},{76,10},{77,9},{77,10},{76,11},{77,11},{78,9},{78,10},{78,11},{87,8},{87,9},{87,10},{87,11},{88,8},{88,9},{88,10},{88,11}};
#define WORD_DOT_WIDTH 95

static void skynet_rgb(cairo_t *cr, double r,double g,double b) {
    cairo_set_source_rgb(cr,r/255,g/255,b/255);
}
static void skynet_point(cairo_t *cr,LogoVec p,int move) {
    double s=.93*1200/(1200-p.z), x=240+p.x*s,y=134+p.y*s;
    if(move) cairo_move_to(cr,x,y); else cairo_line_to(cr,x,y);
}
static void skynet_outline(cairo_t *cr,LogoFace *face) {
    for(int j=0;j<4;++j) skynet_point(cr,face->points[j],j==0);
    cairo_close_path(cr);
}
static void skynet_texture(cairo_t *cr,LogoFace *face,double angle) {
    const LogoVec *plate=logo_plates[face->plate];
    for(int pass=0;pass<2;++pass) {
        if(pass) skynet_rgb(cr,164+88*face->light,18+28*face->light,35+32*face->light);
        else skynet_rgb(cr,46+30*face->light,3,10);
        cairo_set_line_width(cr,1);
        for(double y=-100;y<103;y+=7.5) {
            double cuts[4];int count=0;
            for(int i=0;i<4;++i) {
                LogoVec a=plate[i],b=plate[(i+1)%4];
                if((a.y<=y&&b.y>y)||(b.y<=y&&a.y>y))
                    cuts[count++]=a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);
            }
            if(count!=2) continue;
            double left=fmin(cuts[0],cuts[1])+1.5,right=fmax(cuts[0],cuts[1])-1.5;
            if(right<=left) continue;
            double z=face->surface*14.0;
            if(!pass) {
                skynet_point(cr,logo_rotate((LogoVec){left,y,z},angle),1);
                skynet_point(cr,logo_rotate((LogoVec){right,y,z},angle),0);
            } else for(double x=ceil(left/4.5)*4.5;x+1.3<right;x+=4.5) {
                skynet_point(cr,logo_rotate((LogoVec){x,y,z},angle),1);
                skynet_point(cr,logo_rotate((LogoVec){x+1.3,y,z},angle),0);
            }
        }
        cairo_stroke(cr);
    }
}
static gboolean skynet_draw(GtkWidget *widget,cairo_t *cr,gpointer unused) {
    double width=gtk_widget_get_allocated_width(widget),height=gtk_widget_get_allocated_height(widget);
    double scale=fmin(width/480.,height/340.);
    cairo_save(cr);
    cairo_translate(cr,(width-480*scale)/2,0);
    cairo_scale(cr,scale,scale);
    cairo_set_line_cap(cr,CAIRO_LINE_CAP_ROUND);
    cairo_set_line_join(cr,CAIRO_LINE_JOIN_ROUND);
    double angle=fmod(g_get_monotonic_time()/1000.,8000.)*2*G_PI/8000.;
    LogoFace faces[18];int count=0;
    for(int p=0;p<3;++p) {
        LogoVec front[4],back[4];
        for(int i=0;i<4;++i) {
            front[i]=logo_plates[p][i];front[i].z=14;
            back[3-i]=logo_plates[p][i];back[3-i].z=-14;
        }
        logo_add_face(faces,&count,front,p,1,angle);
        logo_add_face(faces,&count,back,p,-1,angle);
        for(int i=0;i<4;++i) {
            LogoVec a=front[i],b=front[(i+1)%4];
            LogoVec side[4]={a,{a.x,a.y,-14},{b.x,b.y,-14},b};
            logo_add_face(faces,&count,side,p,0,angle);
        }
    }
    for(int i=1;i<count;++i) {
        LogoFace face=faces[i];int j=i;
        while(j>0&&faces[j-1].depth>face.depth){faces[j]=faces[j-1];--j;}
        faces[j]=face;
    }
    for(int i=0;i<count;++i) {
        LogoFace *face=&faces[i];
        if(face->surface) skynet_rgb(cr,16,1,5);
        else skynet_rgb(cr,38+65*face->light,3,12);
        skynet_outline(cr,face);cairo_fill(cr);
        if(face->surface) skynet_texture(cr,face,angle);
        skynet_outline(cr,face);
        skynet_rgb(cr,65+35*face->light,5,17);
        cairo_set_line_width(cr,3);cairo_stroke_preserve(cr);
        skynet_rgb(cr,160+78*face->light,18+32*face->light,34+34*face->light);
        cairo_set_line_width(cr,1);cairo_stroke(cr);
    }
    double spacing=380./WORD_DOT_WIDTH,left=240-WORD_DOT_WIDTH*spacing/2;
    skynet_rgb(cr,218,220,224);
    for(size_t i=0;i<G_N_ELEMENTS(word_dots);++i) {
        cairo_arc(cr,left+word_dots[i][0]*spacing,266+word_dots[i][1]*3.3,1.18,0,2*G_PI);
        cairo_fill(cr);
    }
    cairo_select_font_face(cr,"monospace",CAIRO_FONT_SLANT_NORMAL,CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr,10.5);
    const char *caption="NEURAL NET-BASED ARTIFICIAL INTELLIGENCE";
    cairo_text_extents_t ext;cairo_text_extents(cr,caption,&ext);
    skynet_rgb(cr,164,138,144);
    cairo_move_to(cr,240-ext.width/2-ext.x_bearing,326);
    cairo_show_text(cr,caption);
    cairo_restore(cr);
    return FALSE;
}
static gboolean skynet_tick(GtkWidget *widget,GdkFrameClock *clock,gpointer data) {
    gint64 *last=data,now=gdk_frame_clock_get_frame_time(clock);
    if(now-*last>=33000) {gtk_widget_queue_draw(widget);*last=now;}
    return G_SOURCE_CONTINUE;
}
static GtkWidget *skynet_logo_widget(int height) {
    GtkWidget *area=gtk_drawing_area_new();
    gtk_widget_set_size_request(area,480,height);
    g_signal_connect(area,"draw",G_CALLBACK(skynet_draw),NULL);
    gtk_widget_add_tick_callback(area,skynet_tick,g_new0(gint64,1),g_free);
    return area;
}
