/* Native SKYNET mesh renderer. Draws into the saver pixmap only; no input. */
#ifndef SKYNET_LOGO_H
#define SKYNET_LOGO_H
#include <X11/extensions/Xrender.h>
#include <math.h>

#define LOGO_WIDTH 480
#define LOGO_HEIGHT 260
#define LOGO_AA 2
#define LOGO_PERIOD_MS 8000.0
#define LOGO_PI 3.14159265358979323846

typedef struct { double x, y, z; } LogoVec;
typedef struct {
  LogoVec points[4], normal;
  double depth, light;
  int plate, surface; /* surface: +1 front, -1 back, 0 rim */
} LogoFace;
typedef struct {
  Pixmap buffer;
  Picture source, destination;
  GC gc;
  int left, top, ready;
} Logo;

/* Three separate extruded plates preserve the original SKYNET silhouette. */
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

static XPoint logo_project(LogoVec p) {
  const double scale = 0.93 * 1200.0 / (1200.0 - p.z);
  return (XPoint){(short)lround(LOGO_AA*(LOGO_WIDTH/2.0 + p.x*scale)),
                  (short)lround(LOGO_AA*(134.0 + p.y*scale))};
}

static unsigned long logo_rgb(int r, int g, int b) {
  return ((unsigned long)r << 16) | ((unsigned long)g << 8) | (unsigned long)b;
}

static void logo_destroy(Display *dpy, Logo *logo) {
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
  logo->ready = 1;
}

static int logo_visible(const Logo *logo, const XWindowAttributes *attr) {
  return logo->ready && logo->left < attr->width && logo->top < attr->height &&
         logo->left+LOGO_WIDTH > 0 && logo->top+LOGO_HEIGHT > 0;
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

static void logo_texture(Display *dpy, Logo *logo, const LogoFace *face,
                          double angle) {
  const LogoVec *plate = logo_plates[face->plate];
  XSegment dots[2048], rows[40];
  int dot_count=0, row_count=0;
  /* Dots belong to the plate, so the texture rotates with the solid mesh. */
  for (double y=-100; y<103; y+=7.5) {
    double intersections[4]; int count=0;
    for (int i=0; i<4; ++i) {
      LogoVec a=plate[i], b=plate[(i+1)%4];
      if ((a.y<=y && b.y>y) || (b.y<=y && a.y>y))
        intersections[count++] = a.x+(y-a.y)*(b.x-a.x)/(b.y-a.y);
    }
    if (count!=2) continue;
    double left=fmin(intersections[0],intersections[1])+1.5;
    double right=fmax(intersections[0],intersections[1])-1.5;
    if (right<=left) continue;
    double z=face->surface*14.0;
    XPoint a=logo_project(logo_rotate((LogoVec){left,y,z},angle));
    XPoint b=logo_project(logo_rotate((LogoVec){right,y,z},angle));
    rows[row_count++]=(XSegment){a.x,a.y,b.x,b.y};
    for (double xx=ceil(left/4.5)*4.5; xx+1.3<right; xx+=4.5) {
      if (dot_count >= (int)(sizeof(dots)/sizeof(*dots))) break;
      a=logo_project(logo_rotate((LogoVec){xx,y,z},angle));
      b=logo_project(logo_rotate((LogoVec){xx+1.3,y,z},angle));
      dots[dot_count++]=(XSegment){a.x,a.y,b.x,b.y};
    }
  }
  XSetLineAttributes(dpy,logo->gc,LOGO_AA,LineSolid,CapRound,JoinRound);
  XSetForeground(dpy,logo->gc,logo_rgb(46+(int)(30*face->light),3,10));
  XDrawSegments(dpy,logo->buffer,logo->gc,rows,row_count);
  XSetForeground(dpy,logo->gc,logo_rgb(164+(int)(88*face->light),
                  18+(int)(28*face->light),35+(int)(32*face->light)));
  XDrawSegments(dpy,logo->buffer,logo->gc,dots,dot_count);
}

static void logo_draw(Display *dpy, Window window, XWindowAttributes *attr,
                       Logo *logo, double elapsed_ms) {
  if (!logo_visible(logo,attr)) return;
  double angle=fmod(elapsed_ms,LOGO_PERIOD_MS)*2*LOGO_PI/LOGO_PERIOD_MS;
  LogoFace faces[18]; int count=0;
  for (int p=0; p<3; ++p) {
    LogoVec front[4],back[4];
    for (int i=0; i<4; ++i) {
      front[i]=logo_plates[p][i]; front[i].z=14;
      back[3-i]=logo_plates[p][i]; back[3-i].z=-14;
    }
    logo_add_face(faces,&count,front,p,1,angle);
    logo_add_face(faces,&count,back,p,-1,angle);
    for (int i=0; i<4; ++i) {
      LogoVec a=front[i],b=front[(i+1)%4];
      LogoVec side[4]={a,{a.x,a.y,-14},{b.x,b.y,-14},b};
      logo_add_face(faces,&count,side,p,0,angle);
    }
  }
  /* Paint far surfaces first; three rigid, nonintersecting convex prisms. */
  for (int i=1; i<count; ++i) {
    LogoFace face=faces[i]; int j=i;
    while (j>0 && faces[j-1].depth>face.depth) { faces[j]=faces[j-1]; --j; }
    faces[j]=face;
  }
  XSetForeground(dpy,logo->gc,0);
  XFillRectangle(dpy,logo->buffer,logo->gc,0,0,
                  LOGO_AA*LOGO_WIDTH,LOGO_AA*LOGO_HEIGHT);
  for (int i=0; i<count; ++i) {
    LogoFace *face=&faces[i]; XPoint points[5];
    for (int j=0; j<4; ++j) points[j]=logo_project(face->points[j]);
    points[4]=points[0];
    XSetForeground(dpy,logo->gc,face->surface ? logo_rgb(16,1,5) :
                    logo_rgb(38+(int)(65*face->light),3,12));
    XFillPolygon(dpy,logo->buffer,logo->gc,points,4,Convex,CoordModeOrigin);
    if (face->surface) logo_texture(dpy,logo,face,angle);
    XSetForeground(dpy,logo->gc,logo_rgb(65+(int)(35*face->light),5,17));
    XSetLineAttributes(dpy,logo->gc,3*LOGO_AA,LineSolid,CapRound,JoinRound);
    XDrawLines(dpy,logo->buffer,logo->gc,points,5,CoordModeOrigin);
    XSetForeground(dpy,logo->gc,logo_rgb(160+(int)(78*face->light),
                    18+(int)(32*face->light),34+(int)(34*face->light)));
    XSetLineAttributes(dpy,logo->gc,LOGO_AA,LineSolid,CapRound,JoinRound);
    XDrawLines(dpy,logo->buffer,logo->gc,points,5,CoordModeOrigin);
  }
  XRenderComposite(dpy,PictOpSrc,logo->source,None,logo->destination,
                    0,0,0,0,logo->left,logo->top,LOGO_WIDTH,LOGO_HEIGHT);
  /* Clip negative origins explicitly: XClearArea with unsigned sizes is tricky. */
  int x=logo->left<0?0:logo->left, y=logo->top<0?0:logo->top;
  int right=logo->left+LOGO_WIDTH, bottom=logo->top+LOGO_HEIGHT;
  if (right>attr->width) right=attr->width;
  if (bottom>attr->height) bottom=attr->height;
  XClearArea(dpy,window,x,y,(unsigned)(right-x),(unsigned)(bottom-y),False);
  XFlush(dpy);
}
#endif
