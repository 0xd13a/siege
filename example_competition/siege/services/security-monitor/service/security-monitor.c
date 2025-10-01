//
// CyberSci Nationals 2023
//
// Dmitriy Beryoza (0xd13a)
//
// Defense competition
//
// Security Monitor vulnerable service

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAX_LINE_LENGTH 80
#define STR_BUF_LENGTH  21

#define USER_OPERATOR 0
#define USER_ADMIN    1
#define USER_MAINT    2

#define ALARM_NO 5

#define ALARM_DISARMED  0
#define ALARM_ARMED     1
#define ALARM_TRIGGERED 2

int alarms[ALARM_NO] = {ALARM_ARMED, ALARM_ARMED, ALARM_ARMED, ALARM_ARMED, ALARM_ARMED};

char* alarm_status[] = {"DISARMED", "ARMED", "TRIGGERED"};

typedef struct {
    char username[STR_BUF_LENGTH];
    char password[STR_BUF_LENGTH];
    int type;
} User;

User* users = NULL;
int user_count = 0;
int user_type = 0;

int load_user_info() {
	FILE* file = fopen("sm-users.csv", "r");
    if (file == NULL) {
		printf("\nError loading user info.\n");
        return 0;
    }
    char line[MAX_LINE_LENGTH];

    // Read the file line by line
    while (fgets(line, MAX_LINE_LENGTH, file) != NULL) {

        // Clear the newline character
        line[strcspn(line, "\n")] = 0;

        char* token;
        char* rest = line;
        int columnCount = 0;

        // Split the line by commas and populate the record
        User user;
		char buf[STR_BUF_LENGTH];
        while ((token = strtok_r(rest, ",", &rest)) != NULL) {
            switch (columnCount) {
                case 0:
                    strcpy(user.username, token);
                    break;
                case 1:
                    strcpy(user.password, token);
                    break;
                case 2:
					strcpy(buf, token);
                    user.type = atoi(buf);
                    break;
            }
            columnCount++;
        }

        // Increase the size of the records array and add the new record
        users = realloc(users, (user_count + 1) * sizeof(User));
        users[user_count] = user;
        user_count++;
    }
	
    fclose(file);
	return 1;
}

int check_credentials() {
    struct {
	    char username[STR_BUF_LENGTH];
	    char password[STR_BUF_LENGTH];
	    char unknown;
    } login;

    login.unknown = true;

	printf("Welcome to Can-doo Security Monitoring System\n\n");
	printf("*** Only authorized personnel allowed. ***\n\n");

	printf("Username: "); 

	if (!gets(login.username)) {
		return 0;
	}

	printf("Password: ");

	if (!gets(login.password)) {
		return 0;
	}

	for (int i = 0; i < user_count; i++) {
		if (!strcmp(login.username, users[i].username) &&
		    !strcmp(login.password, users[i].password)) {
			login.unknown = false;
			user_type = users[i].type;
			break;
		}	
	}
	
	if (login.unknown) {
		printf("\n*** Invalid login!\n");
		return 0;
	}
	
	return 1;
}

void display_alarms() {
	printf("\nCurrent alarm status:\n\n");
	printf("1 Station security perimeter - %s\n", alarm_status[alarms[0]]);
	printf("2 Reactor building           - %s\n", alarm_status[alarms[1]]);
	printf("3 Vacuum building            - %s\n", alarm_status[alarms[2]]);
	printf("4 Turbine hall               - %s\n", alarm_status[alarms[3]]);
	printf("5 Emergency power generators - %s\n", alarm_status[alarms[4]]);
}

int get_alarm_no() {
	
	int choice;
	char val[5];
	if (!gets(val)) {
		return 0;
	}
	choice = atoi(val);
	
	if ((choice >= 1) && (choice <= 5))
		return choice;
	else
		return 0;
}

void trigger_alarm() {
	display_alarms();
	
	printf("\nSelect the alarm to trigger: ");

	int alarm = get_alarm_no();
	if (alarm != 0) {
		alarms[alarm-1] = ALARM_TRIGGERED;
	}
} 

void clear_alarm() {
	display_alarms();
	
	printf("\nSelect the alarm to clear: ");

	int alarm = get_alarm_no();
	if (alarm != 0) {
		alarms[alarm-1] = ALARM_ARMED;
	}
}

void disarm_alarms() {
	printf("\n*** Disabling all alarms! ***\n");
	
	for(int i = 0; i < ALARM_NO; i++) {
		alarms[i] = ALARM_DISARMED;
	}		
}


void display_menu() {
	printf("\nSelect one of the following options\n\n");
	printf("1 - Exit\n");
	printf("2 - Display alarm status\n");
	printf("3 - Trigger alarm (Admin access required)\n");
	printf("4 - Clear alarm (Admin access required)\n");
	printf("5 - Shut down alarm system (Maintenance access required)\n");
	printf("> ");
}

uint get_menu_choice(int max_value) {

    do {
		display_menu();
		
		int choice;
		char val[5];
		if (!gets(val)) {
			printf("\n*** Error entering value!\n");
			continue;
		}
		choice = atoi(val);
		
		if (choice > max_value) {
			printf("\n*** Menu item number too high!\n");
			continue;
		}

        return choice;

    } while(1);
}

void handle_menu() {
	
	uint choice;
	
	do {

		choice = get_menu_choice(5);
		
		if (choice < 1) {
			printf("\n*** Menu item number too low!\n");
			continue;
		}

		if (choice == 1) {
			printf("Goodbye.\n");
			break;
		}
	
		if (choice == 2) {
			display_alarms();
			continue;
		}

		if (choice == 3) {
			trigger_alarm();
			continue;
		}
	
		if (choice == 4) {
			clear_alarm();
			continue;
		}

		if ((choice == 5) && (user_type != USER_MAINT)) {
			printf("\n*** User must be a maintenance technician!\n");
			continue;
		}

		disarm_alarms();
		
	} while (1);
	
}

int main(int argc, char* argv[]) {

	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);
	
	if (!load_user_info()) {
		return 1;
	}

	if (!check_credentials()) 
		return 1;

	handle_menu();
	
	return 0;
}