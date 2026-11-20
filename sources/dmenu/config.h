/* See LICENSE file for copyright and license details. */
/* Default settings; can be overriden by command line. */

static int topbar = 1;                      /* -b  option; if 0, dmenu appears at bottom     */
/* -fn option overrides fonts[0]; default X11 font or font set */
static const char *fonts[] = {
	"JetBrains Mono:size=13"
};
static const char *prompt      = "EXEC";    /* -p  option; prompt to the left of input field */
static const char *colors[SchemeLast][2] = {
	/*     fg         bg       */
	[SchemeNorm] = { "#D3D6DA", "#070809" },
	[SchemeSel] = { "#FFFFFF", "#AE2031" },
	[SchemeOut] = { "#FFFFFF", "#481722" },
	/* SKYNET panel: dim frame/rails, bright corners and cursor, steel footer */
	[SchemeFrame] = { "#69222E", "#070809" },
	[SchemeAccent] = { "#FF4050", "#070809" },
	[SchemeDim] = { "#6E7A86", "#070809" },
};
/* -l option; if nonzero, dmenu uses vertical list with given number of lines */
static unsigned int lines      = 12;

/*
 * Characters not considered part of a word while deleting words
 * for example: " /?\"&[]"
 */
static const char worddelimiters[] = " ";

/* SKYNET panel: used when centred with a vertical list (-c/-t toggle) */
static int centered = 1;
static const unsigned int hudwidth  = 760;  /* panel width in pixels      */
static const unsigned int hudpad    = 14;   /* inner padding              */
static const unsigned int hudgap    = 10;   /* space around the red rails */
static const unsigned int hudcorner = 18;   /* corner bracket length      */
static const unsigned int rowpad    = 10;   /* extra height per row       */
static const char *hudlabel = "SKYNET // LAUNCH CONTROL";
