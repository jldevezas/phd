#
# Configurations and constants.
#

baseDir <- "~/Desktop/lastfm-dataset-1K"

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
monthly.ranks <- list()
adoption.by.rank <- list()
hourly.total.plays <- data.frame(user=character(), hour=character(), plays=character());

for (user.id in users$id) {
  print(paste("Processing ", user.id, "...", sep=""))
  
  # Songs listened by the user.
  songs <- read.table(paste(paste(baseDir, user.id, sep="/"), "csv", sep="."), quote="", sep="\t", fill=T)
  names(songs) <- c("id", "timestamp", "artid", "artname", "traid", "traname")
  songs$month <- strftime(as.Date(songs$timestamp), "%Y-%m")
  songs$hour <- as.numeric(format(as.POSIXct(songs$timestamp, format="%Y-%m-%dT%H:%M:%SZ"), format="%H"))
  
  # Hourly number of plays for each user.
  user.hourly.total.plays <- with(songs, aggregate(id, by=list(hour), length))
  names(user.hourly.total.plays) <- c("hour", "plays")
  hourly.total.plays <- rbind(hourly.total.plays, cbind(user=rep(user.id, 24), AddZeroHours(user.hourly.total.plays)))
  
  # Monthly number of plays for each artist.
  monthly.artist.plays[[user.id]] <- with(songs, aggregate(artname, by=list(month, artname), length))
  names(monthly.artist.plays[[user.id]]) <- c("month", "artist", "plays")
  
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
# To make it readable only.
norm.hourly.plays.by.country <- norm.hourly.plays.by.country[with(norm.hourly.plays.by.country, order(country, hour)), ]

# Offset to country timezone (TODO make into reusable function).

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

png(file=paste(baseDir, "hourly_scrobbles_by_gender.png", sep="/"), width=900, height=350)
ggplot(hourly.plays.by.gender[order(hourly.plays.by.gender$gender), ], aes(x=factor(hour), y=plays, fill=gender)) +
  geom_bar(stat="identity") +
  scale_fill_manual(name="Gender", labels=c("NA", "Female", "Male"), values=c("gray40", "violetred2", "skyblue1")) +
  labs(x="Hour of the Day", y="Number of Scrobbled Songs") +
  guides(fill = guide_legend(reverse = TRUE)) +
  theme_gray(base_size = 14, base_family="Ubuntu Medium")
dev.off()

png(file=paste(baseDir, "hourly_scrobbles_by_country.png", sep="/"), width=900*3, height=2000*3)
ggplot(norm.hourly.plays.by.country, aes(x=hour, y=plays, fill=as.factor(cluster))) +
  geom_bar(stat="identity") +
  scale_fill_brewer(name="Behavior Type", palette=2, type="qual") +
  facet_wrap( ~ country, ncol=4) +
  labs(x="Hour of the Day", y="Number of Scrobbled Songs") +
  theme_gray(base_size = 14*3, base_family="Ubuntu Medium") +
  theme(legend.position="top")
dev.off()


#
# Write results to files.
#
                   
write.csv(user.stats, file=paste(baseDir, "user-stats.csv", sep="/"), row.names=FALSE)                   
write.csv(hourly.total.plays, file=paste(baseDir, "hourly-plays.csv", sep="/"), row.names=FALSE)

for (user.id in users$id) {
  print(paste("Writing analysis data for ", user.id, "...", sep=" "))
  
  # Top overall artists.
  overall.ranks <- with(monthly.artist.plays[[user.id]], aggregate(artist, by=list(artist), length))
  names(overall.ranks) <- c("artist", "plays")
  overall.ranks <- overall.ranks[order(overall.ranks$plays, decreasing=T),]
  
  # Fill the monthly time series with zeros for missing values and export to CSV.
  write.csv(AddZeroMonths(monthly.artist.plays[[user.id]][
    which(monthly.artist.plays[[user.id]]$artist %in% overall.ranks[1:20, ]$artist),]),
          file=paste(paste(baseDir, user.id, sep="/"), "_monthly_activity.csv", sep=""),
          row.names=FALSE)
}


#
# Clean up temporary variables.
#

rm(i, j, user.id, plays, month, artists, overall.ranks, songs, user.adoption.by.rank)