#
# LastFm Data Analysis
# José Devezas (joseluisdevezas@gmail.com)
#
# Based on the Last.fm Dataset -- 1K Users, by Oscar Celma.
# Available here: http://www.dtic.upf.edu/~ocelma/MusicRecommendationDataset/lastfm-1K.html
#


#
# Configurations and constants.
#

baseDir <- "~/Desktop/lastfm-dataset-1K"
outputDir <- "~/Desktop/lastfm-dataset-1K/output"

# Dates range from 2005-02-14 00:00:07 to 2013-09-29 18:32:04.
maxMonthRange <- c("2005-02", "2013-09")


#
# Utility functions.
#

IsAnyNA <- function(vals) {
  for(val in vals)
    if (is.na(val))
      return(TRUE)
  return(FALSE)
}

AddZeroMonths <- function(d, month.range=NA) {
  if (IsAnyNA(month.range))
    month.range <- range(d$month)
    
  all.months <- as.character(seq(as.Date(paste(month.range[1], "01", sep="-")),
                                as.Date(paste(month.range[2], "01", sep="-")),
                                by="1 month"))
  all.months <- unlist(lapply(all.months, function(month) {
    d <- strsplit(month, "-")[[1]]
    paste(d[1], d[2], sep="-")
  }))
  all.artists <- unique(d$artist)
  
  result <- data.frame(month = c(sapply(all.months, function(m) rep(m, length(all.artists)))))
  result <- cbind(result, artist = rep(all.artists, length(all.months)))
  result <- merge(d, result, by.x=c("month", "artist"), by.y=c("month", "artist"), all.y=TRUE)
  na.pos <- which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays <- 0
  
  return(result)
}

AddZeroWeekdays <- function(d) {
  all.artists <- unique(d$artist)
  
  result <- data.frame(weekday = c(sapply(0:6, function(m) rep(m, length(all.artists)))))
  result <- cbind(result, artist = rep(all.artists, 7))
  result <- merge(d, result, by.x=c("weekday", "artist"), by.y=c("weekday", "artist"), all.y=TRUE)
  na.pos <- which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays <- 0
  
  return(result)
}

AddZeroHours <- function(d) {
  result <- data.frame(hour=0:23)
  result <- merge(d, result, by=c("hour"), all=TRUE)
  na.pos <- which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays <- 0
  return(result)
}

RotateHour <- function(hour, offset) {
  new.hour <- hour + offset
  
  if (new.hour < 0 || new.hour > 23) {
    new.hour <- new.hour - 24 * (new.hour %/% 24)
  }
  
  return (new.hour)
}

weekdays <- factor(c("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"),
                   levels=c("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"))
Weekdays <- function(weekdays.numeric) {
  paste(weekdays[unique(weekdays.numeric)], sep="/", collapse="/")
}

# Try to determine if an artist has a preferred play weekday for the given user.
WeeklyAnalysis <- function(df, user.id, artist, charts=FALSE, info=FALSE,
                           approve.threshold=1.5, reject.range=c(0, 0.1)) {
  udf <- AddZeroWeekdays(df[[user.id]])
  user.plays <- aggregate(udf$plays, by=list(udf$weekday), sum)$x
  user.plays <- user.plays / max(user.plays)  
  
  plays <- AddZeroWeekdays(df[[user.id]][
    which(df[[user.id]]$artist == artist), ])$plays
  plays <- plays / max(plays) * (1 / user.plays)
  
  listens <- data.frame(weekday=0:6, score=as.numeric(apply(
    sapply(plays, function(e) plays - e * approve.threshold), 1, sum)))
  listens$accept <- listens$score > 0
  
  if (charts) {
    #par(mfrow=c(1, 2))
    #barplot(user.plays, names.arg=weekdays[1:7])
    #title(user.id)
    #barplot(listens$score, names.arg=weekdays[listens$weekday+1], col=palette()[as.numeric(listens$accept) + 1])
    #title(paste(user.id, artist, sep="+"))
    #print(listens)
    
    require("ggplot2")
    filename <- paste("preferred_listening_weekday_", user.id, "_", artist, ".png", sep="")
    png(file=paste(outputDir, filename, sep="/"), width=450, height=350)
    print(ggplot(listens, aes(x=weekdays[weekday+1], y=score, fill=factor(accept, levels=c(T, F)))) +
            geom_bar(stat="identity") +
            labs(x="Weekdays", y="Overall Distance Score") +
            scale_fill_brewer(name="Accept", palette="Dark2") +
            theme_gray(base_size = 14, base_family="Ubuntu Medium") +
            theme(legend.position="top"))
    dev.off()
    
    filename <- paste(user.id, "_weekly_scrobbles.png", sep="")
    png(file=paste(outputDir, filename, sep="/"), width=450, height=350)
    print(ggplot(data.frame(weekday=0:6, plays=user.plays), aes(x=weekdays[weekday+1], y=plays)) +
            geom_bar(stat="identity") +
            labs(x="Weekdays", y="Plays (Normalized by Maximum)") +
            theme_gray(base_size = 14, base_family="Ubuntu Medium") +
            theme(legend.position="top"))
    dev.off()
  }
  
  ret <- list(user.id=user.id,
              artist=artist,
              preferred.listening.weekdays="",
              avoided.listening.weekdays="",
              mean.plays=mean(plays),
              sd.plays=sd(plays),
              var.plays=var(plays))

  wd <- which(listens$accept)
  if (length(wd) >= 1 && length(wd) <= 3) {
    if (info) {
      print(paste(artist, "is a", Weekdays(wd), "artist for", user.id))
    }
    ret$preferred.listening.weekdays <- Weekdays(listens$weekday[wd]+1)
  } else if (info) {
    print(paste(user.id, "doesn't have a specific weekday to listen to", artist))
  }
  
  wd <- which(plays >= reject.range[1] & plays <= reject.range[2])
  if (length(wd) >= 1 && length(wd) <= 3) {
    if (info) {
      print(paste(user.id, "nearly doesn't listen to", artist, "on", Weekdays(wd)))
    }
    ret$avoided.listening.weekdays <- Weekdays(listens$weekday[wd]+1)
  }

  return(ret)
}


#
# Dataset analysis.
#

users <- read.table(gzfile(paste(baseDir, "userid-profile.tsv.gz", sep="/")), quote="", sep="\t")
names(users) <- c("id", "gender", "age", "country", "registered")

#-------

user.stats <- data.frame(id=levels(users$id),
                        unique.artists=rep(NA, nrow(users)),
                        plays.total=rep(NA, nrow(users)),
                        plays.min=rep(NA, nrow(users)),
                        plays.qua1=rep(NA, nrow(users)),
                        plays.median=rep(NA, nrow(users)),
                        plays.mean=rep(NA, nrow(users)),
                        plays.qua3=rep(NA, nrow(users)),
                        plays.max=rep(NA, nrow(users)))

monthly.artist.plays <- list()
weekly.artist.plays <- list()
monthly.ranks <- list()
adoption.by.rank <- list()
overall.ranks <- list()
hourly.total.plays <- data.frame(user=character(), hour=character(), plays=character());

for (user.id in users$id) {
  print(paste("Processing ", user.id, "...", sep=""))
  
  # Ranked artists per user.
  overall.ranks[[user.id]] <- with(monthly.artist.plays[[user.id]], aggregate(artist, by=list(artist), length))
  names(overall.ranks[[user.id]]) <- c("artist", "plays")
  overall.ranks[[user.id]] <- overall.ranks[[user.id]][order(overall.ranks[[user.id]]$plays, decreasing=T),]
  
  # Songs listened by the user.
  songs <- read.table(paste(paste(baseDir, user.id, sep="/"), "csv", sep="."), quote="", sep="\t", fill=T)
  names(songs) <- c("id", "timestamp", "artid", "artname", "traid", "traname")
  songs$month <- strftime(as.Date(songs$timestamp), "%Y-%m")
  songs$weekday <- strftime(as.Date(songs$timestamp), "%w")
  songs$hour <- as.numeric(format(as.POSIXct(songs$timestamp, format="%Y-%m-%dT%H:%M:%SZ"), format="%H"))
  
  # Hourly number of plays for each user.
  user.hourly.total.plays <- with(songs, aggregate(id, by=list(hour), length))
  names(user.hourly.total.plays) <- c("hour", "plays")
  hourly.total.plays <- rbind(hourly.total.plays, cbind(user=rep(user.id, 24), AddZeroHours(user.hourly.total.plays)))
  
  # Monthly number of plays for each artist, per user.
  monthly.artist.plays[[user.id]] <- with(songs, aggregate(artname, by=list(month, artname), length))
  names(monthly.artist.plays[[user.id]]) <- c("month", "artist", "plays")
  
  # Weekly number of plays for each artist, per user.
  weekly.artist.plays[[user.id]] <- with(songs, aggregate(artname, by=list(weekday, artname), length))
  names(weekly.artist.plays[[user.id]]) <- c("weekday", "artist", "plays")

  # Unique artists listened by the user.
  user.stats[which(user.stats$id == user.id),]$unique.artists <- nlevels(monthly.artist.plays[[user.id]]$artist)
  
  # Statistics for the play count of the user.
  user.stats[which(user.stats$id == user.id),]$plays.total <- sum(monthly.artist.plays[[user.id]]$plays)
  user.stats[which(user.stats$id == user.id), 4:9] <- summary(monthly.artist.plays[[user.id]]$plays)
        
  # Monthly artist ranks.
  monthly.ranks[[user.id]] <- aggregate(songs$artname, by=list(songs$month), function(artname) {
    plays <- table(artname)
    names(sort(plays, decreasing=TRUE))
  })
  names(monthly.ranks[[user.id]]) <- c("month", "ranks")
    
  # How well do favorite monthly artists rank ahead in time?
  # (This score measures adpotion by considering not only if an artist is listened to again
  # in the future, but also how much it's listened to compared to other artists.)
  user.adoption.by.rank <- list()
  for (i in 1:(nrow(monthly.ranks[[user.id]]$ranks))) {
    user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] <- 0
    for (j in 1:(nrow(monthly.ranks[[user.id]]$ranks))) {
      if (i < j & monthly.ranks[[user.id]]$month[i] < monthly.ranks[[user.id]]$month[j]) {
        if (monthly.ranks[[user.id]]$ranks[i, 1] %in% monthly.ranks[[user.id]]$ranks[j,]) {
          user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] <-
            user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] + 1 * 1/j
        }
      }
    }
  }
  user.adoption.by.rank <- sort(unlist(user.adoption.by.rank)/max(unlist(user.adoption.by.rank)), decreasing=TRUE)
  adoption.by.rank[[user.id]] <- user.adoption.by.rank
}

hourly.total.plays <- merge(hourly.total.plays, users[, c(1,2,4)], by.x="user", by.y="id", all=TRUE)

# How consistently are favorite monthly artists listened to ahead in time?
# (Measure variance ahead of time?)
# user.id <- "user_000271"
# for (month in monthly.ranks[[user.id]]$month) {
#   top.artist <- monthly.ranks[[user.id]][which(monthly.ranks[[user.id]]$month == month), 2][1]
#   after.month.artist.plays <- AddZeroMonths(monthly.artist.plays[[user.id]][
#     which(monthly.artist.plays[[user.id]]$month > month), ])
#   after.month.top.artist.plays <- after.month.artist.plays[which(after.month.artist.plays$artist == top.artist), ]
#   month.top.artist.future.variance <- var(after.month.top.artist.plays$plays)
#   month.top.artist.future.total <- sum(after.month.top.artist.plays$plays)
#   n.months <- length(unique(after.month.top.artist.plays$month))
#   print(paste(user.id, month, top.artist,
#               month.top.artist.future.variance,
#               month.top.artist.future.total,
#               month.top.artist.future.variance / n.months * month.top.artist.future.total / n.months,
#               sep=' | '))
# }


#
# Identify weekdays that show a different behavior from the remaining.
#

weekly.analysis <- list()
for (user.id in users$id) {
  print(paste("Processing", user.id))
  
  weekly.analysis[[user.id]] <- data.frame(artist=character(0),
                                           preferred.listening.weekdays=character(0),
                                           avoided.listening.weekdays=character(0),
                                           mean.plays=numeric(0),
                                           sd.plays=numeric(0),
                                           var.plays=numeric(0))
  
  # DELETEME This is now precomputed, since it's used so often.
  # Top overall artists.
  #overall.ranks <- with(monthly.artist.plays[[user.id]], aggregate(artist, by=list(artist), length))
  #names(overall.ranks) <- c("artist", "plays")
  #overall.ranks <- overall.ranks[order(overall.ranks$plays, decreasing=T),]
  
  for (artist in head(overall.ranks[[user.id]], 50)$artist) {
    new.data <- WeeklyAnalysis(weekly.artist.plays, user.id, artist)
    weekly.analysis[[user.id]]$artist <- as.character(weekly.analysis[[user.id]]$artist)
    weekly.analysis[[user.id]]$preferred.listening.weekdays <-
      as.character(weekly.analysis[[user.id]]$preferred.listening.weekdays)
    weekly.analysis[[user.id]]$avoided.listening.weekdays <-
      as.character(weekly.analysis[[user.id]]$avoided.listening.weekdays)
    weekly.analysis[[user.id]] <- rbind(weekly.analysis[[user.id]], new.data)
  }
}


#
# Write results to files.
#

write.csv(user.stats, file=paste(outputDir, "user-stats.csv", sep="/"), row.names=FALSE)                   
write.csv(hourly.total.plays, file=paste(outputDir, "hourly-plays.csv", sep="/"), row.names=FALSE)


for (user.id in users$id) {
  print(paste("Writing analysis data for ", user.id, "...", sep=""))
  
  write.csv(weekly.analysis[[user.id]],
            file=paste(outputDir, paste(user.id, "_weekly_analysis.csv", sep=""), sep="/"),
            row.names=FALSE)  
  
  # DELETEME This is now precomputed, since it's used so often.
  # Top overall artists.
  #overall.ranks <- with(monthly.artist.plays[[user.id]], aggregate(artist, by=list(artist), length))
  #names(overall.ranks) <- c("artist", "plays")
  #overall.ranks <- overall.ranks[order(overall.ranks$plays, decreasing=T),]
  
  # Fill the monthly time series with zeros for missing values and export to CSV.
  # UNTESTED overall.ranks
  write.csv(AddZeroMonths(monthly.artist.plays[[user.id]][
    which(monthly.artist.plays[[user.id]]$artist %in% overall.ranks[[user.id]][1:20, ]$artist),]),
            file=paste(paste(outputDir, user.id, sep="/"), "_monthly_activity.csv", sep=""),
            row.names=FALSE)
  
  # Fill the weekly time series with zeros for missing values and export to CSV.
  write.csv(AddZeroWeekdays(weekly.artist.plays[[user.id]][
    which(weekly.artist.plays[[user.id]]$artist %in% overall.ranks[[user.id]][1:20, ]$artist),]),
            file=paste(paste(outputDir, user.id, sep="/"), "_weekly_activity.csv", sep=""),
            row.names=FALSE)
}


#
# Compute hourly scrobbles by country.
#

plays.by.country <- tapply(hourly.total.plays$plays, hourly.total.plays$country, sum)
hourly.plays.by.country <- aggregate(hourly.total.plays$plays,
                                     by=list(hourly.total.plays$country, hourly.total.plays$hour), sum)
names(hourly.plays.by.country) <- c("country", "hour", "plays")

norm.hourly.plays.by.country <- hourly.plays.by.country
norm.hourly.plays.by.country$plays <- norm.hourly.plays.by.country$plays /
  plays.by.country[norm.hourly.plays.by.country$country]
# These are, in fact, valid locations, but Netherlands Antilles has too little data. United States Minor
# Outlying Islands should however be added back in the next run (or replaced by a country with few data).
not.country <- c("", "Netherlands Antilles", "United States Minor Outlying Islands")
norm.hourly.plays.by.country <- norm.hourly.plays.by.country[
  -which(norm.hourly.plays.by.country$country %in% not.country), ]
norm.hourly.plays.by.country$country <- factor(norm.hourly.plays.by.country$country, levels=country.rank)
country.rank <- names(sort(plays.by.country, decreasing=TRUE))
country.rank <- country.rank[-which(country.rank %in% not.country)]


#
# Offset to country timezone (TODO make into reusable function).
#

country.codes <- read.csv(paste(baseDir, "timezonedb/country.csv", sep="/"), head=FALSE)
names(country.codes) <- c("country.code", "country")

zones <- read.csv(paste(baseDir, "timezonedb/zone.csv", sep="/"), head=FALSE)
names(zones) <- c("zone.id", "country.code", "zone.name")

time.zones <- read.csv(paste(baseDir, "timezonedb/timezone.csv", sep="/"), head=FALSE)
names(time.zones) <- c("zone.id", "abbreviation", "time.start", "gmt.offset", "dst")

tzdb <- merge(merge(country.codes, zones), time.zones)
levels(tzdb$country)[which(levels(tzdb$country) == "Russia")] <- "Russian Federation"
levels(tzdb$country)[which(levels(tzdb$country) == "Democratic Republic of the Congo")] <-
  "Congo, the Democratic Republic of the"
levels(tzdb$country)[which(levels(tzdb$country) == "North Korea")] <-
  "Korea, Democratic People's Republic of"

for (country in country.rank) {
  country.zone.ids <- unique(tzdb[which(as.character(tzdb$country) == country), ]$zone.id)
  
  if (country == "Cote D'Ivoire") {
    # Not in tzdb, but offset is zero, so we can skip it.
    next
  }
  
  hour.offset <- round(mean(unique(tzdb[which(
    tzdb$zone.id %in% country.zone.ids & tzdb$time.start > as.numeric(Sys.time())), ]$gmt.offset)) / 3600)
  norm.hourly.plays.by.country[which(norm.hourly.plays.by.country$country == country), ]$hour <-
    sapply(norm.hourly.plays.by.country[which(norm.hourly.plays.by.country$country == country), ]$hour,
           function(h) RotateHour(h, hour.offset))
}

# Reorder for better readability.
norm.hourly.plays.by.country <- norm.hourly.plays.by.country[with(norm.hourly.plays.by.country, order(country, hour)), ]

#
# Cluster hourly music listening behavior by country.
#
# We're thinking of this kind of like a time series clustering problem, except that
# they are in phase already and normalized, so the problem becomes easier. Biggest
# challenge is to identify the number of clusters, but since our data is so small,
# we can simply use silhouette to find the best k.
#

require(cluster)

dp <- matrix(nrow=length(country.rank), ncol=24)
rownames(dp) <- country.rank
colnames(dp) <- paste(0:23, "h", sep="")
for (country in country.rank) {
  dp[country, ] <- norm.hourly.plays.by.country[which(norm.hourly.plays.by.country$country == country), "plays"]
}

cl <- list()
sil <- array()
for (k in 2:6) {
  cl[[k]] <- kmeans(dp, k)
  sil[k] <- summary(silhouette(cl[[k]]$cluster, dist(dp)))$avg.width
}
best.cluster <- cl[[which.max(sil)]]
norm.hourly.plays.by.country$cluster <- best.cluster$cluster[norm.hourly.plays.by.country$country]


#
# Compute hourly scrobbles by genre.
#

hourly.plays.by.gender <- aggregate(hourly.total.plays$plays,
                                    by=list(hourly.total.plays$country,
                                            hourly.total.plays$gender,
                                            hourly.total.plays$hour),
                                    sum)
names(hourly.plays.by.gender) <- c("country", "gender", "hour", "plays")
hourly.plays.by.gender <- hourly.plays.by.gender[-which(hourly.plays.by.gender$country %in% not.country), ]

for (country in country.rank) {
  country.zone.ids <- unique(tzdb[which(as.character(tzdb$country) == country), ]$zone.id)
  
  if (country == "Cote D'Ivoire") {
    # Not in tzdb, but offset is zero, so we can skip it.
    next
  }
  
  hour.offset <- round(mean(unique(tzdb[which(
    tzdb$zone.id %in% country.zone.ids & tzdb$time.start > as.numeric(Sys.time())), ]$gmt.offset)) / 3600)
  hourly.plays.by.gender[which(hourly.plays.by.gender$country == country), ]$hour <-
    sapply(hourly.plays.by.gender[which(hourly.plays.by.gender$country == country), ]$hour,
           function(h) RotateHour(h, hour.offset))
}

hourly.plays.by.gender <- aggregate(hourly.plays.by.gender$plays, by=list(
  hourly.plays.by.gender$gender, hourly.plays.by.gender$hour), sum)
names(hourly.plays.by.gender) <- c("gender", "hour", "plays")


#
# Beautiful charts.
#

require(ggplot2)

png(file=paste(outputDir, "hourly_scrobbles_by_gender.png", sep="/"), width=900, height=350)
ggplot(hourly.plays.by.gender[order(hourly.plays.by.gender$gender), ], aes(x=factor(hour), y=plays, fill=gender)) +
  geom_bar(stat="identity") +
  scale_fill_manual(name="Gender", labels=c("NA", "Female", "Male"), values=c("gray40", "violetred2", "skyblue1")) +
  labs(x="Hour of the Day", y="Number of Scrobbled Songs") +
  guides(fill = guide_legend(reverse = TRUE)) +
  theme_gray(base_size = 14, base_family="Ubuntu Medium")
dev.off()

png(file=paste(outputDir, "hourly_scrobbles_by_country.png", sep="/"), width=900*3, height=2000*3)
ggplot(norm.hourly.plays.by.country, aes(x=hour, y=plays, fill=as.factor(cluster))) +
  geom_bar(stat="identity") +
  scale_fill_brewer(name="Behavior Type", palette=2, type="qual") +
  facet_wrap( ~ country, ncol=4) +
  labs(x="Hour of the Day", y="Fraction of Scrobbled Songs") +
  theme_gray(base_size = 14*3, base_family="Ubuntu Medium") +
  theme(legend.position="top")
dev.off()

require(RColorBrewer)
pal <- brewer.pal(3, name="Dark2")

png(file=paste(outputDir, "hourly_scrobbles_by_country_behavior_1.png", sep="/"), width=900, height=350)
center <- data.frame(hour=0:23, plays=as.numeric(best.cluster$centers[1, ]))
ggplot(center) +
  geom_bar(aes(x=hour, y=plays), fill=pal[1], stat="identity") +
  labs(x="Hour of the Day", y="Fraction of Scrobbled Songs") +
  theme_gray(base_size = 14, base_family="Ubuntu Medium") +
  theme(legend.position="top")
dev.off()

png(file=paste(outputDir, "hourly_scrobbles_by_country_behavior_2.png", sep="/"), width=900, height=350)
center <- data.frame(hour=0:23, plays=as.numeric(best.cluster$centers[2, ]))
ggplot(center) +
  geom_bar(aes(x=hour, y=plays), fill=pal[2], stat="identity") +
  labs(x="Hour of the Day", y="Fraction of Scrobbled Songs") +
  theme_gray(base_size = 14, base_family="Ubuntu Medium") +
  theme(legend.position="top")
dev.off()


#
# Posterior analysis.
#

# Are the countries grouped in a cluster simply because of having more than one time zone?
sapply(names(best.cluster$cluster[which(best.cluster$cluster == 1)]), function(country) {
  country.zone.ids <- unique(tzdb[which(as.character(tzdb$country) == country), ]$zone.id)
  length(unique(tzdb[which(tzdb$zone.id %in% country.zone.ids
                           & tzdb$time.start > as.numeric(Sys.time())), ]$gmt.offset))
  })


#
# Clean up temporary variables.
#

rm(i, j, user.id, plays, month, artists, songs, user.adoption.by.rank)