#!/bin/bash

# Crawls Google Play App store to find popular apps (many ratings)
# with low scores.
#
# Make sure you have a dictionary at $DICTIONARY

set -e

NUM_SEARCHES=${1:-10}
DICTIONARY=~/dictionary.txt
PERCENTILE=20

mkdir -p apps

# search for random words and retrieve some data about matching apps

for word in $(sort -R $DICTIONARY | head -n $NUM_SEARCHES); do

    apps=$(curl -s "https://play.google.com/store/search?q=${word}&c=apps&hl=en" |
		  egrep -o '\/store\/apps\/details\?id=([a-z.]+)"' |
		  sed -E 's/.*id=([a-z.]+).*/\1/' |
		  sort |
		  uniq)

    for app in $apps; do

	test -d apps/$app && echo $app is OLD OLD OLD && continue

	mkdir apps/$app

	curl -s "https://play.google.com/store/apps/details?id=${app}&hl=en" > poop

	egrep -o 'span class="reviews-num" aria-label=" ([0-9,]+) ratings' poop |
	    sed -E 's/.* ([0-9,]+) ratings/\1/' > apps/$app/ratings
	egrep -o 'div class="score" aria-label=" Rated ([0-9.]+) stars out of five stars' poop |
	    sed -E 's/.* Rated ([0-9.]+).*/\1/' > apps/$app/score
	egrep -o "<meta content=\"[a-zA-Z0-9', ]+.*\" name=\"description\">" poop |
	    sed -E "s/.*content=\"([a-zA-Z0-9', ]+).*\".*/\1/" > apps/$app/summary

	rm poop

	if ! test -s apps/$app/score || \
		! test -s apps/$app/ratings || \
		! test -s apps/$app/summary; then
	    rm -r apps/$app
	    continue
	fi

	echo $app $(<apps/$app/score) $(<apps/$app/ratings)
    done
done


# find the lowest scored among the most rated apps

> ratings_name.tmp
for app in $(ls -1 apps/); do
    echo $(<apps/$app/ratings) $app >> ratings_name.tmp
done
sort -n ratings_name.tmp > ratings_name.tmp2

N=$(cat ratings_name.tmp2 | wc -l)
M=$(echo "$N * $PERCENTILE / 100.0" | bc | cut -d. -f1)

>score_name.tmp
for app in $(tail -n $M ratings_name.tmp2 | awk '{print $2}'); do
   echo $(<apps/$app/score) $app >> score_name.tmp
done

sort -n score_name.tmp | awk '{print $2}' > popular.tmp

N=$(cat popular.tmp | wc -l)
M=$(echo "$N * $PERCENTILE / 100.0" | bc | cut -d. -f1)

>report.txt
for app in $(head -n $M popular.tmp); do
    echo -e "$app \t $(<apps/$app/summary) \t $(<apps/$app/ratings) \t $(<apps/$app/score)"  >> report.txt
done

rm score_name.tmp ratings_name.tmp ratings_name.tmp2 popular.tmp

echo Report created in report.txt
