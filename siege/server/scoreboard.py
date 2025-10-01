#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# Siege Competition Framework
#
# Author: Dmitriy Beryoza (0xd13a)

import traceback

from jinja2 import Environment, FileSystemLoader, Template
from siege.core.log import log, log_error
from siege.core.tick_results import TickResults
from siege.server.scoring_policy import ScoringPolicy, TargetScore
from siege.server.server_config import ServerConfig
from siege.core.util import get_sorted_values, to_millis
from siege.server.server_results_db import ServerResultDB

OVERALL_TEAM_ID = 0
OVERALL_SCORE = 1
OVERALL_TICK_SINCE = 2


class CompetitionScore:
    place: int
    team_id: int
    team_name: str
    score: int

    def __init__(self, place: int, team_id: int, team_name: str,
                 score: int) -> None:
        self.place = place
        self.team_id = team_id
        self.team_name = team_name
        self.score = score


class ChartScore:
    team_id: int
    time: int
    score: int

    def __init__(self, team_id: int, time: int, score: int) -> None:
        self.team_id = team_id
        self.time = time
        self.score = score


class TeamScore:
    time: int
    tick: int
    details: dict[int, TargetScore]
    score: int

    def __init__(self, time: int, tick: int, details: dict[int, TargetScore],
                 score: int) -> None:
        self.time = time
        self.tick = tick
        self.details = details
        self.score = score

    def get_ordered_target_scores(self) -> list[TargetScore]:
        return get_sorted_values(self.details)


INDEX_TEMPLATE = "index-template.jinja"            # Index page template
SCOREBOARD_TEMPLATE = "scoreboard-template.jinja"  # Scoreboard page template
TEAM_TEMPLATE = "team-template.jinja"              # Team page template

# Database file name
DB = "scoreboard.db"


# Scoreboard object that encapsulates competition management logic
class Scoreboard:

    received_results: dict[int, list[TickResults]] = {}  # Received results
    config: ServerConfig
    scoring_policy: ScoringPolicy
    server_db: ServerResultDB
    index_template: Template             # Index page template
    main_scoreboard_template: Template   # Scoreboard template
    team_scoreboard_template: Template   # Team template

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.scoring_policy = ScoringPolicy(self.config, self.received_results)
        self.server_db = ServerResultDB(self.config.get_data_folder() / DB)

        # Pre-load page templates
        file_loader = FileSystemLoader(self.config.get_source_site_folder())
        env = Environment(loader=file_loader)
        self.index_template = env.get_template(INDEX_TEMPLATE)
        self.main_scoreboard_template = env.get_template(SCOREBOARD_TEMPLATE)
        self.team_scoreboard_template = env.get_template(TEAM_TEMPLATE)

        # Initialize scoreboard with team sections
        for team_id in self.config.get_team_ids():
            self.received_results[team_id] = []

        # Load the database if it exists
        tick_results = self.server_db.load_database()

        # If database exists - load scores, scoreboard must have been
        # restarted for some reason
        for result in tick_results:
            res = TickResults.from_str(result[0])
            self.consume_result(res)

    def consume_result(self, result: TickResults) -> None:
        """ Consume submitted result (from bot or database). """

        team_id = result.get_team_id()
        tick = result.get_tick()

        # If this data for existing score entry
        if tick <= (len(self.received_results[team_id])-1):
            # Are we replacing missing entry?
            if len(self.received_results[team_id][tick].get_results()) == 0:
                log("[team {}, tick {}] Overwriting empty result with {}".
                    format(team_id, tick, result))
                self.received_results[team_id][tick] = result
            return

        # Do we have previous missing score entries? Fill them in.
        while tick > len(self.received_results[team_id]):
            log("[team {}, tick {}] Adding empty result".
                format(team_id, len(self.received_results[team_id])))
            self.received_results[team_id].append(
                TickResults(team_id, len(self.received_results[team_id])))

        # Add score
        log("[team {}, tick {}] Adding result {}".
            format(team_id, tick, result))
        self.received_results[team_id].append(result)

        # Save result to database
        self.server_db.save_score(result)

    def build_team_page_scores(self, team_id: int) -> list[TeamScore]:
        """ Build scores for individual team. """

        team_scores: list[TeamScore] = []
        prepared_scores = self.scoring_policy.calculate_scores(team_id)

        for row in prepared_scores:
            team_scores.append(
                TeamScore(
                    to_millis(self.config.tick2time(row.get_tick())),
                    row.get_tick(), row.get_target_scores(),
                    row.get_tick_score()))

        # Show most recent results first
        team_scores.reverse()

        return team_scores

    def build_chart_scores(self) -> list[ChartScore]:
        """ Build scores to use in the chart. """
        team_scores = []
        # For every team
        for team_id in self.config.get_team_ids():

            prepared_scores = self.scoring_policy.calculate_scores(team_id)

            for row in prepared_scores:
                team_scores.append(ChartScore(team_id, to_millis(
                    self.config.tick2time(row.get_tick())),
                    row.get_tick_score()))

        return team_scores

    def build_competition_scores(self) -> list[CompetitionScore]:
        """ Build scores for Defense competition. """

        # Collect all scores
        team_scores = []
        for team_id in range(len(self.received_results)):

            prepared_scores = self.scoring_policy.calculate_scores(team_id)

            # Take the latest result
            score = 0
            tick_since = 0

            if len(prepared_scores) != 0:
                current = prepared_scores[len(prepared_scores)-1]
                score = current.get_tick_score()
                tick_since = current.get_tick_since()

            team_scores.append((team_id, score, tick_since))

        enriched_team_scores = []

        # Sort results by "last seen" tick number (lowest first), and then by
        # score. This is done in order to break ties so that the team that
        # achieved a particular score earlier would win. This approach works
        # because of sort stability (see https://docs.python.org/3/howto/
        # sorting.html#sort-stability-and-complex-sorts)
        sorted_team_scores = sorted(team_scores,
                                    key=lambda tup: tup[OVERALL_TICK_SINCE])
        sorted_team_scores = sorted(sorted_team_scores,
                                    key=lambda tup: tup[OVERALL_SCORE],
                                    reverse=True)

        # Build final result structure
        first_record = True
        prev_score = -1
        prev_tick = -1
        place = 1
        for team_score in sorted_team_scores:
            if not first_record:
                if (team_score[OVERALL_SCORE] != prev_score) \
                        or (team_score[OVERALL_TICK_SINCE] != prev_tick):
                    place += 1

            enriched_team_scores.append(
                CompetitionScore(place, team_score[OVERALL_TEAM_ID],
                                 self.config.get_team(
                                     team_score[OVERALL_TEAM_ID]).get_name(),
                                 team_score[OVERALL_SCORE]))

            first_record = False
            prev_score = team_score[OVERALL_SCORE]
            prev_tick = team_score[OVERALL_TICK_SINCE]

        return enriched_team_scores

    def write_file(self, name: str, content: str) -> None:
        """ Produce the full path for the file. """
        filename = self.config.get_site_folder() / name

        # Replace saved version
        try:
            open(filename, "w").write(content)
        except Exception:
            log_error("Error writing file '{}': {}".
                      format(filename, traceback.format_exc()))

    def set_up(self) -> None:
        # Produce the landing page
        index_rendered = self.index_template.render(
            targets=self.config.get_targets(),
            start_time=to_millis(self.config.get_start_time()),
            end_time=to_millis(self.config.get_end_time()),
            prep_start=to_millis(self.config.get_prep_start()),
            prep_minutes=self.config.get_prep_minutes(),
            score_cap=self.config.get_score_cap(),
            negative_score_cap=self.config.get_negative_score_cap(),
            successful_benign_points=self.config.
            get_successful_benign_points(),
            failed_benign_points=self.config.get_failed_benign_points(),
            successful_malicious_points=self.config.
            get_successful_malicious_points(),
            failed_malicious_points=self.config.get_failed_malicious_points(),
            down_points=self.config.get_down_points())
        self.write_file("index.html", index_rendered)

    def generate_files(self, banner: str) -> None:
        """ Generate HTML files. """

        # Prepare data
        competition_scores = self.build_competition_scores()
        chart_scores = self.build_chart_scores()

        # Render main scoreboard
        rendered = self.main_scoreboard_template.render(
            banner=banner,
            competition_scores=competition_scores,
            chart_scores=chart_scores,
            start_time=to_millis(self.config.get_start_time()),
            end_time=to_millis(self.config.get_end_time()),
            teams=self.config.get_teams(),
            competition_finished=self.config.event_finished())

        # Replace saved version
        self.write_file("scoreboard.html", rendered)

        # Render team's scores
        for team in self.config.get_teams():
            team_scores = self.build_team_page_scores(team.get_id())
            rendered = self.team_scoreboard_template.render(
                banner=banner, team_name=team.get_name(),
                targets=self.config.get_targets(), team_scores=team_scores,
                competition_finished=self.config.event_finished())

            # Replace saved version
            self.write_file("team{}.html".format(team.get_id()), rendered)
