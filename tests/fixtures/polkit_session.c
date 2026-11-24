/* Exercise only optional session registration, never the system authority. */
#define main authentication_agent_main
#include "main.c"
#undef main

int main(void)
{
    return register_client_to_gnome_session() ? 0 : 1;
}
