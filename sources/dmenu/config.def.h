/* See LICENSE file for copyright and license details. */
/* Default settings; can be overriden by command line. */

static int topbar = 1;                      /* -b  option; if 0, dmenu appears at bottom     */
/* -fn option overrides fonts[0]; default X11 font or font set */
static const char *fonts[] = {
	"monospace:size=10"
};
static const char *prompt      = NULL;      /* -p  option; prompt to the left of input field */
static const char *colors[SchemeLast][2] = {
	/*     fg         bg       */
	[SchemeNorm] = { "#bbbbbb", "#222222" },
	[SchemeSel] = { "#eeeeee", "#005577" },
	[SchemeOut] = { "#000000", "#00ffff" },
	[SchemeFrame] = { "#444444", "#222222" },
	[SchemeAccent] = { "#eeeeee", "#222222" },
	[SchemeDim] = { "#888888", "#222222" },
};
/* -l option; if nonzero, dmenu uses vertical list with given number of lines */
static unsigned int lines      = 0;

/*
 * Characters not considered part of a word while deleting words
 * for example: " /?\"&[]"
 */
static const char worddelimiters[] = " ";

/* centred panel; used only with -c and a vertical list */
static int centered = 0;
static const unsigned int hudwidth  = 760;
static const unsigned int hudpad    = 14;
static const unsigned int hudgap    = 10;
static const unsigned int hudcorner = 18;
static const unsigned int rowpad    = 10;
static const char *hudlabel = "dmenu";
