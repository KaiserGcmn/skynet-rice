/* See LICENSE file for copyright and license details. */
#include <X11/XF86keysym.h>

/* appearance */
static const unsigned int borderpx  = 4;        /* REDLINE: hard window borders */
static const unsigned int barpadding = 12;      /* total vertical bar padding */
static const unsigned int barlinepx  = 3;       /* red rail below the bar */
static const unsigned int statuspadding = 8;   /* horizontal inset per panel */
static const unsigned int statusgap = 3;       /* black separator between panels */
static const unsigned int snap      = 32;       /* snap pixel */
static const int showbar            = 1;        /* 0 means no bar */
static const int topbar             = 1;        /* 0 means bottom bar */
static const unsigned int systraypinning = 0;   /* 0: sloppy systray follows selected monitor, >0: pin systray to monitor X */
static const unsigned int systrayonleft = 0;    /* 0: systray in the right corner, >0: systray on left of status text */
static const unsigned int systrayspacing = 2;   /* systray spacing */
static const int systraypinningfailfirst = 1;   /* 1: if pinning fails, display systray on the first monitor, False: display systray on the last monitor*/
static const int showsystray        = 1;     /* 0 means no systray */
/* REDLINE INDUSTRIAL: steel dividers, block labels, signal-red rail. */
static const char *fonts[]          = { "JetBrains Mono:style=ExtraBold:size=13" };
static const char dmenufont[]       = "JetBrains Mono:style=ExtraBold:size=13";
static const char col_gray1[]       = "#070809";
static const char col_gray2[]       = "#393D42";
static const char col_gray3[]       = "#D3D6DA";
static const char col_gray4[]       = "#FFFFFF";
static const char col_selbg[]       = "#C3131C";
static const char col_selborder[]   = "#FF1B22";
static const char dmenu_bg[]        = "#070809";
static const char dmenu_selbg[]     = "#D21920";
static const char *colors[][3]      = {
	/*               fg         bg         border   */
	[SchemeNorm] = { col_gray3, col_gray1, col_gray2 },
	[SchemeSel]  = { col_gray4, col_selbg, col_selborder },
	[SchemeStatusCPU]  = { "#E1E5EA", "#101318", "#3B444F" },
	[SchemeStatusCPUBadge] = { "#FFFFFF", "#A51420", "#FF3B38" },
	[SchemeStatusCPUMeter] = { "#FF3B38", "#2B333E", "#3B444F" },
	[SchemeStatusBAT]  = { "#D3D8DE", "#0B0D10", col_selborder },
	[SchemeStatusBATMeter] = { "#FF3B38", "#0B0D10", col_selborder },
	[SchemeStatusBATCell1] = { "#FF3B38", "#0B0D10", col_selborder },
	[SchemeStatusBATCell2] = { "#FF5956", "#0B0D10", col_selborder },
	[SchemeStatusBATCell3] = { "#FF7774", "#0B0D10", col_selborder },
	[SchemeStatusBATCell4] = { "#FF9592", "#0B0D10", col_selborder },
	[SchemeStatusBATCell5] = { "#FFB3B0", "#0B0D10", col_selborder },
	[SchemeStatusDate] = { "#D3D6DA", "#20242A", col_gray2 },
	[SchemeStatusTime] = { "#FFFFFF", col_selbg, col_selborder },
};

/* tagging */
static const char *tags[] = { "[01]", "[02]", "[03]", "[04]", "[05]", "[06]" };

static const Rule rules[] = {
	/* xprop(1):
	 *	WM_CLASS(STRING) = instance, class
	 *	WM_NAME(STRING) = title
	 */
	/* class      instance    title       tags mask     isfloating   monitor */
	{ "Gimp",     NULL,       NULL,       0,            1,           -1 },
	{ "floorp",    NULL,       NULL,       0,            0,           -1 },
};

/* layout(s) */
static const float mfact     = 0.55; /* factor of master area size [0.05..0.95] */
static const int nmaster     = 1;    /* number of clients in master area */
static const int resizehints = 1;    /* 1 means respect size hints in tiled resizals */
static const int lockfullscreen = 1; /* 1 will force focus on the fullscreen window */
static const int refreshrate = 120;  /* refresh rate (per second) for client move/resize */

static const Layout layouts[] = {
	/* symbol     arrange function */
	{ "[TILE]",   tile },    /* first entry is default */
	{ "[FLOAT]",  NULL },    /* no layout function means floating behavior */
	{ "[MONO]",   monocle },
};

/* key definitions */
#define MODKEY Mod1Mask
#define TAGKEYS(KEY,TAG) \
	{ MODKEY,                       KEY,      view,           {.ui = 1 << TAG} }, \
	{ MODKEY|ControlMask,           KEY,      toggleview,     {.ui = 1 << TAG} }, \
	{ MODKEY|ShiftMask,             KEY,      tag,            {.ui = 1 << TAG} }, \
	{ MODKEY|ControlMask|ShiftMask, KEY,      toggletag,      {.ui = 1 << TAG} },

/* helper for spawning shell commands in the pre dwm-5.0 fashion */
#define SHCMD(cmd) { .v = (const char*[]){ "/bin/sh", "-c", cmd, NULL } }

/* commands */
static char dmenumon[2] = "0"; /* component of dmenucmd, manipulated in spawn() */
static const char *dmenucmd[] = { "dmenu_run", "-m", dmenumon, "-fn", dmenufont, "-nb", dmenu_bg, "-nf", col_gray3, "-sb", dmenu_selbg, "-sf", col_gray4, NULL };
static const char *termcmd[]  = { "kitty", NULL };
static const char *flameshotcmd[] = { "flameshot", "gui", NULL };

static const Key keys[] = {
	/* modifier                     key        function        argument */
	/* Audio hotkeys sent by Fn+F1..F4; leave plain F1..F4 to applications. */
	{ 0,                            XF86XK_AudioRaiseVolume, spawn, SHCMD("/usr/local/bin/dwm-volume up") },
	{ 0,                            XF86XK_AudioLowerVolume, spawn, SHCMD("/usr/local/bin/dwm-volume down") },
	{ 0,                            XF86XK_AudioMute,        spawn, SHCMD("/usr/local/bin/dwm-volume mute") },
	{ 0,                            XF86XK_AudioMicMute,     spawn, SHCMD("/usr/local/bin/dwm-volume mic-mute") },
	/* Brightness hotkeys sent by Fn+F5/F6; plain F5/F6 stay available to applications. */
	{ 0,                            XF86XK_MonBrightnessDown, spawn, SHCMD("/usr/local/bin/dwm-brightness down") },
	{ 0,                            XF86XK_MonBrightnessUp,   spawn, SHCMD("/usr/local/bin/dwm-brightness up") },
	{ MODKEY,                       XK_p,      spawn,          {.v = dmenucmd } },
        { MODKEY,                       XK_Return, spawn, {.v = termcmd } },
	{ MODKEY,                       XK_b,      togglebar,      {0} },
	{ MODKEY,                       XK_j,      focusstack,     {.i = +1 } },
	{ MODKEY,                       XK_k,      focusstack,     {.i = -1 } },
	{ MODKEY,                       XK_i,      incnmaster,     {.i = +1 } },
	{ MODKEY,                       XK_d,      incnmaster,     {.i = -1 } },
	{ MODKEY,                       XK_h,      setmfact,       {.f = -0.05} },
	{ MODKEY,                       XK_l,      setmfact,       {.f = +0.05} },
	{ MODKEY,                       XK_Return, zoom,           {0} },
	{ MODKEY,                       XK_Tab,    view,           {0} },
	{ MODKEY,                       XK_q,      killclient,     {0} },
	{ MODKEY,                       XK_t,      setlayout,      {.v = &layouts[0]} },
	{ MODKEY,                       XK_f,      setlayout,      {.v = &layouts[1]} },
	{ MODKEY,                       XK_m,      setlayout,      {.v = &layouts[2]} },
	{ MODKEY,                       XK_space,  setlayout,      {0} },
	{ MODKEY|ShiftMask,             XK_space,  togglefloating, {0} },
	{ MODKEY,                       XK_0,      view,           {.ui = ~0 } },
	{ MODKEY|ShiftMask,             XK_0,      tag,            {.ui = ~0 } },
	{ MODKEY,                       XK_comma,  focusmon,       {.i = -1 } },
	{ MODKEY,                       XK_period, focusmon,       {.i = +1 } },
	{ MODKEY|ShiftMask,             XK_comma,  tagmon,         {.i = -1 } },
	{ MODKEY|ShiftMask,             XK_period, tagmon,         {.i = +1 } },
	TAGKEYS(                        XK_1,                      0)
	TAGKEYS(                        XK_2,                      1)
	TAGKEYS(                        XK_3,                      2)
	TAGKEYS(                        XK_4,                      3)
	TAGKEYS(                        XK_5,                      4)
	TAGKEYS(                        XK_6,                      5)
	TAGKEYS(                        XK_7,                      6)
	TAGKEYS(                        XK_8,                      7)
	TAGKEYS(                        XK_9,                      8)
	{ MODKEY|ShiftMask,             XK_q,      quit,           {0} },
        { 0,                            XK_Print,  spawn,          {.v = flameshotcmd } },
};

/* button definitions */
/* click can be ClkTagBar, ClkLtSymbol, ClkStatusText, ClkWinTitle, ClkClientWin, or ClkRootWin */
static const Button buttons[] = {
	/* click                event mask      button          function        argument */
	{ ClkLtSymbol,          0,              Button1,        setlayout,      {0} },
	{ ClkLtSymbol,          0,              Button3,        setlayout,      {.v = &layouts[2]} },
	{ ClkWinTitle,          0,              Button2,        zoom,           {0} },
	{ ClkStatusText,        0,              Button2,        spawn,          {.v = termcmd } },
	{ ClkClientWin,         MODKEY,         Button1,        movemouse,      {0} },
	{ ClkClientWin,         MODKEY,         Button2,        togglefloating, {0} },
	{ ClkClientWin,         MODKEY,         Button3,        resizemouse,    {0} },
	{ ClkTagBar,            0,              Button1,        view,           {0} },
	{ ClkTagBar,            0,              Button3,        toggleview,     {0} },
	{ ClkTagBar,            MODKEY,         Button1,        tag,            {0} },
	{ ClkTagBar,            MODKEY,         Button3,        toggletag,      {0} },
};
