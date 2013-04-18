is.any.na = function(vals) {
  for(val in vals)
    if (is.na(val))
      return(TRUE)
  return(FALSE)
}

f.expand.artists.months.with.zeros = function(d, month.range=NA) {
  if (is.any.na(month.range))
    month.range = range(d$month)
  
  # TODO
}

# Dates range from 2005-02-14 00:00:07 to 2013-09-29 18:32:04.
max.month.range = c("2005-02", "2013-09")

users = read.table(gzfile("~/Desktop/lastfm-dataset-1K/userid-profile.tsv.gz"), quote="", sep="\t")
names(users) = c("id", "gender", "age", "country", "registered")

# Data for user 1 only (users were cut into separate files using split-by-user.py).
songs = read.table("~/Desktop/lastfm-dataset-1K/user_000003.csv", quote="", sep="\t")
names(songs) = c("id", "timestamp", "artid", "artname", "traid", "traname")
songs$month = strftime(as.Date(songs$timestamp), "%Y-%m")

# Monthly number of plays for each artist.
monthly.artist.plays = with(songs, aggregate(artname, by=list(month, artname), length))
names(monthly.artist.plays) = c("month", "artist", "plays")

# Monthly favorite artists.
monthly.favorite = with(monthly.artist.plays, aggregate(plays, by=list(month), function(monthly.plays) artist[which.max(monthly.plays)]))
monthly.favorite$artist = as.character(monthly.favorite$artist)
names(monthly.favorite) = c("month", "artist")

# Monthly artist ranks.
monthly.ranks = aggregate(songs$artname, by=list(songs$month), function(artname) {
  plays = table(artname)
  names(sort(plays, decreasing=TRUE))
})
names(monthly.ranks) = c("month", "ranks")

# How well do favorite monthly artists rank ahead in time?
# (This score measures adpotion by considering not only if an artist is listened to again
# in the future, but also how much it's listened to compared to other artists.)
adoption.by.rank = list()
for (i in 1:(nrow(monthly.ranks$ranks)-1)) {
  adoption.by.rank[[monthly.ranks$ranks[i,1]]] = 0
  for (j in 1:(nrow(monthly.ranks$ranks)-1)) {
    if (i < j & monthly.ranks$month[i] < monthly.ranks$month[j]) {
      if (monthly.ranks$ranks[i,1] %in% monthly.ranks$ranks[j,]) {
        adoption.by.rank[[monthly.ranks$ranks[i,1]]] = adoption.by.rank[[monthly.ranks$ranks[i,1]]] + 1 * 1/j
      }
    }
  }
}
adoption.by.rank = sort(unlist(adoption.by.rank)/max(unlist(adoption.by.rank)), decreasing=TRUE)

# How consistently are favorite monthly artists listened to ahead in time?
# (Measure variance ahead of time?)
# result = list()
# for (i in 1:(nrow(monthly.favorite)-1)) {
#   result[[monthly.favorite[i,]$artist]] = mean(result[[monthly.favorite[i,]$artist]],
#     var(monthly.artist.plays[which(
#       monthly.artist.plays$month > monthly.favorite[i,]$month
#       & monthly.artist.plays$artist == monthly.favorite[i,]$artist),]$plays), na.rm=TRUE)
# }
# result = sort(unlist(result), decreasing=TRUE)