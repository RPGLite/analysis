# High-level overview

This dataset contains a json formatted dump of data collected by players in the mobile game RPGLite.
It contains three high-level attributes: 'players', 'games', and 'page_hits'. No personal information was collected, and none is provided.

'players' contains information about the players of the game.
'games' contains a record of all completed games from the game's release until 24/09/2020.
'page_hits' contains a record of player interactions with the application deployed on Android and iOS devices.


# Player data
Player data is a list of json objects, each with the attributes:

'Username' -- player's username
'Played' -- count of games played
'Won' -- count of games won
'tag_bg' -- background used on player nametags
'Games' -- game documents active at time of capture
'count_character_has_won' -- games won using each character
'count_character_has_been_played' -- games played using each character
'accepting_games' -- whether the player is permitting other players to create new games against them
'skill_points' -- skill points accumulated
'last_logged_in' -- time player last logged into RPGLite
'badge_progressions' -- information pertaining to progression to collecting badges
'elo' -- ELO calculation for player
'lost_against' -- other players this player lost against recently and has not subsequently won against. Repeated entries for repeated losses.
'current_season_skill' -- skill accumulated since season 2 of RPGLite began.


# Game data
Game data is a list of json objects, each with the attributes:

'p1' -- internal ID for player1
'p2' -- internal ID for player2
'p1_selected' -- whether p1 selected characters on capture
'p2_selected' -- whether p1 selected characters on capture
'p1_turn' -- bool representing whether it is currently p1's turn (if not, it's p2's turn)
'Moves' -- moves made through the game
'active_player' -- currently active player
'most recent activity' -- current activity, a list including the datetime of the last move made and the player who made it.
'p1c1' -- player 1's first character chosen
'p1c2' -- player 1's second character chosen 
'p1c1_health' -- player 1's 1st character health
'p1c2_health' -- player 1's 2st character health
'p2c1_health' -- player 2's 1st character health
'p2c2_health' -- player 2's 2st character health
'usernames' -- list of usernames for both players, in order (p1 is element 0, p2 is element 1)


# Page hit data
Page hit data is a list of json objects, each guaranteed to have the attributes 'kind' and 'time'. 'time' reprents the time the datapoint was collected, and 'kind' describes a kind of interaction with the application. Depending on the 'kind' of page_hit collected, extra attributes may also exist. Valid kinds are:

'home_screen_logout'
'registration'
'tabbed_to_find_opponents'
'challenge_sent'
'login'
'joined_queue'
'hs_refresh_pressed'
'searching_from_find_games'
'searched_for_opponent'
'home_to_choose_chars'
'character_selected'
'char_select_to_home'
'home_to_gameplay'
'rolls_fastforwarded'
'move_viewed'
'online_game_to_home'
'home_screen_to_customise_tag'
'customise_tag'
'customise_tag_to_home'
'home_screen_to_profile'
'tabbed_to_history'
'home_screen_to_leaderboard'
'game_history_checked'
'refresh_online_game_pressed'
'home_to_tutorial'
'accepting_games_toggled'
'view_website_from_settings'
'home_screen_to_practice_select'
'practice_character_selected'
'practice_selection_to_game'
'practice_move_viewed'
'practice_rolls_fastforwarded'
'practice_game_over'
'practice_gameover_to_home'
'logged_in'
'message_of_the_day_seen'
'reward_screen_seen'
'view_website_from_registration'
'tutorial_prompt_dismissed'
'left_queue'
'practice_char_select_to_home'
'game_abandoned'
'tutorial_prompt_dismissed_forever'
'practice_game_show_moves'
'gameover_viewed'
'gameover_to_home'
'practice_game_to_home'
'opponent_searched_from_history'
'profile_to_home'
'leaderboard_to_home'
'leaderboard_user_zoom'
'leaderboard_user_zoom_match_attempted'
'practice_gameover_play_again'
'badge_pressed'
'character_deselected'
'practice_character_deselected'
'purging_slot'
'change_password'
'season_1_leaderboard_viewed'
'move_made'
'notifications_toggled'
'konami'
'dev_secret'
