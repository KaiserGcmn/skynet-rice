/* Native rotating SKYNET emblem and scanning caption; saver pixmap only. */
#ifndef SKYNET_LOGO_H
#define SKYNET_LOGO_H
#include <X11/extensions/Xrender.h>
#include <math.h>

#define LOGO_WIDTH 480
#define LOGO_HEIGHT 260
#define LOGO_AA 2
#define LOGO_PERIOD_MS 4000.0
#define LOGO_CAPTION_PERIOD_MS 3800.0

typedef struct {
  Pixmap buffer;
  Picture source, destination;
  GC gc;
  XftDraw *text_draw;
  XftFont *font;
  XftColor dim, bright;
  int left, top, ready, text_colors;
} Logo;

static const double logo_plates[3][4][2] = {
  {{0,-104}, {62,-38}, {0,24}, {-62,-38}},
  {{-74,-32}, {-9,32}, {-9,102}, {-190,102}},
  {{74,-32}, {190,102}, {9,102}, {9,32}}
};

static void logo_destroy(Display *dpy, Logo *logo) {
  if (logo->text_draw) XftDrawDestroy(logo->text_draw);
  if (logo->font) XftFontClose(dpy, logo->font);
  if (logo->text_colors) {
    XftColorFree(dpy, DefaultVisual(dpy, DefaultScreen(dpy)), DefaultColormap(dpy, DefaultScreen(dpy)), &logo->dim);
    XftColorFree(dpy, DefaultVisual(dpy, DefaultScreen(dpy)), DefaultColormap(dpy, DefaultScreen(dpy)), &logo->bright);
  }
  if (logo->destination) XRenderFreePicture(dpy, logo->destination);
  if (logo->source) XRenderFreePicture(dpy, logo->source);
  if (logo->gc) XFreeGC(dpy, logo->gc);
  if (logo->buffer) XFreePixmap(dpy, logo->buffer);
  memset(logo, 0, sizeof(*logo));
}

static void logo_init(Display *dpy, Window window, XWindowAttributes *attr,
                       XImage *image, Pixmap pixmap, Logo *logo) {
  logo_destroy(dpy, logo);
  /* The current artwork is centered, not scaled, by paint(). */
  if (!image || image->width != 1920 || image->height != 1200) return;
  int event_base, error_base;
  if (!XRenderQueryExtension(dpy, &event_base, &error_base)) return;
  XRenderPictFormat *src = XRenderFindStandardFormat(dpy, PictStandardRGB24);
  XRenderPictFormat *dst = XRenderFindVisualFormat(dpy, attr->visual);
  if (!src || !dst) return;
  logo->left = attr->width/2 - LOGO_WIDTH/2;
  logo->top = (attr->height-image->height)/2 + 64;
  logo->buffer = XCreatePixmap(dpy, window, LOGO_AA*LOGO_WIDTH,
                               LOGO_AA*LOGO_HEIGHT, 24);
  logo->gc = XCreateGC(dpy, logo->buffer, 0, NULL);
  logo->source = XRenderCreatePicture(dpy, logo->buffer, src, 0, NULL);
  logo->destination = XRenderCreatePicture(dpy, pixmap, dst, 0, NULL);
  XTransform transform = {{{XDoubleToFixed(LOGO_AA),0,0},
                           {0,XDoubleToFixed(LOGO_AA),0},
                           {0,0,XDoubleToFixed(1)}}};
  XRenderSetPictureTransform(dpy, logo->source, &transform);
  XRenderSetPictureFilter(dpy, logo->source, FilterBilinear, NULL, 0);
  int screen=DefaultScreen(dpy);
  logo->font=XftFontOpenName(dpy,screen,"JetBrains Mono:style=Bold:pixelsize=18");
  logo->text_draw=XftDrawCreate(dpy,logo->buffer,DefaultVisual(dpy,screen),DefaultColormap(dpy,screen));
  if(XftColorAllocName(dpy,DefaultVisual(dpy,screen),DefaultColormap(dpy,screen),"#33060a",&logo->dim)) {
    if(XftColorAllocName(dpy,DefaultVisual(dpy,screen),DefaultColormap(dpy,screen),"#efeff4",&logo->bright))
      logo->text_colors=1;
    else XftColorFree(dpy,DefaultVisual(dpy,screen),DefaultColormap(dpy,screen),&logo->dim);
  }
  logo->ready = 1;
}

static int logo_visible(const Logo *logo, const XWindowAttributes *attr) {
  return logo->ready && logo->left < attr->width && logo->top < attr->height &&
         logo->left+LOGO_WIDTH > 0 && logo->top+LOGO_HEIGHT > 0;
}

/* Match the greeter's vertical-axis rotation; no text or window transforms. */
static void logo_project(double x,double y,double cosine,double sine,double *px,double *py) {
  double perspective=2400./(2400.+(x-240)*sine);
  *px=240+(x-240)*cosine*perspective;
  *py=134+(y-134)*perspective;
}

static void logo_draw(Display *dpy, Window window, XWindowAttributes *attr,
                       Logo *logo, double elapsed_ms) {
  if (!logo_visible(logo,attr)) return;
  double angle=fmod(elapsed_ms,LOGO_PERIOD_MS)*(6.28318530717958647692/LOGO_PERIOD_MS);
  double cosine=cos(angle),sine=sin(angle);
  XSetForeground(dpy,logo->gc,0);
  XFillRectangle(dpy,logo->buffer,logo->gc,0,0,
                  LOGO_AA*LOGO_WIDTH,LOGO_AA*LOGO_HEIGHT);
  XSetForeground(dpy,logo->gc,0xff0000);
  for(int plate=0;plate<3;++plate) {
    XPoint points[4];
    for(int point=0;point<4;++point) {
      double x,y;
      logo_project(240+logo_plates[plate][point][0]*.93,
                   134+logo_plates[plate][point][1]*.93,cosine,sine,&x,&y);
      points[point]=(XPoint){(short)lround(LOGO_AA*x),(short)lround(LOGO_AA*y)};
    }
    Region region=XPolygonRegion(points,4,EvenOddRule);
    if(!region) continue;
    XSetRegion(dpy,logo->gc,region);
    for(double y=30;y<232;y+=9.5) {
      const double corners[4][2]={{40,y},{440,y},{440,y+6.2},{40,y+6.2}};
      XPoint stripe[4];
      for(int point=0;point<4;++point) {
        double px,py;
        logo_project(corners[point][0],corners[point][1],cosine,sine,&px,&py);
        stripe[point]=(XPoint){(short)lround(LOGO_AA*px),(short)lround(LOGO_AA*py)};
      }
      XFillPolygon(dpy,logo->buffer,logo->gc,stripe,4,Convex,CoordModeOrigin);
    }
    XSetClipMask(dpy,logo->gc,None);
    XDestroyRegion(region);
  }
  if(logo->font && logo->text_draw && logo->text_colors) {
    const char *caption="CYBERDYNE SYSTEMS CORPORATION";
    XGlyphInfo extents;
    XftTextExtentsUtf8(dpy,logo->font,(const FcChar8 *)caption,(int)strlen(caption),&extents);
    int left=(LOGO_AA*LOGO_WIDTH-extents.xOff)/2;
    XftDrawStringUtf8(logo->text_draw,&logo->dim,logo->font,left,252*LOGO_AA,
                      (const FcChar8 *)caption,(int)strlen(caption));
    double phase=fmod(elapsed_ms,LOGO_CAPTION_PERIOD_MS)/LOGO_CAPTION_PERIOD_MS;
    int sweep=(int)lround((-10+phase*500)*LOGO_AA);
    XRectangle clip={(short)sweep,236*LOGO_AA,60*LOGO_AA,22*LOGO_AA};
    XftDrawSetClipRectangles(logo->text_draw,0,0,&clip,1);
    XftDrawStringUtf8(logo->text_draw,&logo->bright,logo->font,left,252*LOGO_AA,
                      (const FcChar8 *)caption,(int)strlen(caption));
    XftDrawSetClip(logo->text_draw,NULL);
  }
  XRenderComposite(dpy,PictOpSrc,logo->source,None,logo->destination,
                    0,0,0,0,logo->left,logo->top,LOGO_WIDTH,LOGO_HEIGHT);
  int x=logo->left<0?0:logo->left, y=logo->top<0?0:logo->top;
  int right=logo->left+LOGO_WIDTH, bottom=logo->top+LOGO_HEIGHT;
  if(right>attr->width) right=attr->width;
  if(bottom>attr->height) bottom=attr->height;
  XClearArea(dpy,window,x,y,(unsigned)(right-x),(unsigned)(bottom-y),False);
  XFlush(dpy);
}
#endif
