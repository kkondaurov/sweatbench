# Close-history judgment upgrade

Create milestone-6 reports from operations whose commit and event order disagree, capture them, and
upgrade the database to milestone 7. Closing must preserve those reports exactly. A correction first
committed after close must use the first open day and remain stable across retry and restart.
