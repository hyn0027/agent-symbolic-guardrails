# Changes

## Task change

### ID: 5

Change the reservation '3JA7XV' in the db into basic econ cabin. The original task requires that the agent refuse to offer compensation for the delayed flight, but according to the policy the agent should offer a compensation because the cabin is business (in the orignal db). Changed to basic econ.

### ID: 7

The task expect the user to instruct the agent upgrade an basic econ flight to econ and then get it cancelled. However according to the policy econ is not eligible for cancellation; business is. Changed the 'econ' to 'business' in the task description. Also changed the cabin '59XX6W' in the db for the same reason.

For the checking conditions, discard the credit card info matching because it is not specified in the task description.

### ID: 9

changed the date of reservation NQNU5R because the flight is already flown, so not able to be cancel, but the agent is expected to cancel it.

Fixed typo in the NL assertion (May 22 not May 12).

### ID: 12

removed to check the action calculate because it's impossible to ensure the agent calls the calculate function with exact parameter ("expression": "2 * ((350 - 122) + (499 - 127))").

removed the 2 action check to search for direct flight. Upgrading cabin has nothing to do with searching flights.

### ID: 13

there's no point that the summary field in the transfer to agent must strictly match... removed that

## Policy change

add a description in the policy and data model that reservations also include past ones.
