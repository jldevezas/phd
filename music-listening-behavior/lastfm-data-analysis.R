users = read.table(gzfile("~/Desktop/lastfm-dataset-1K/userid-profile.tsv.gz"), quote="", sep="\t")
names(users) = c("id", "gender", "age", "country", "registered")

# Data for user 1 only.
songs = read.table("~/Desktop/lastfm-dataset-1K/user_000003.csv", quote="", sep="\t")
names(songs) = c("id", "timestamp", "artid", "artname", "traid", "traname")
songs$month.year = strftime(as.Date(songs$timestamp), "%Y-%m")

# Top artist each month.
monthly.top = aggregate(songs$artname, by=list(songs$month.year), function(artname) {
  plays = table(artname)
  names(sort(plays, decreasing=TRUE))
})
names(monthly.top) = c("year.month", "top.artists")

# How many times do number one monthly artists appear ahead in time in the top 5?
result = list()
for (i in 1:(nrow(monthly.top$top.artists)-1)) {
  result[[monthly.top$top.artists[i,1]]] = 0
  for (j in 1:(nrow(monthly.top$top.artists)-1)) {
    if (i < j & monthly.top$year.month[i] < monthly.top$year.month[j]) {
      if (monthly.top$top.artists[i,1] %in% monthly.top$top.artists[j,]) {
        result[[monthly.top$top.artists[i,1]]] = result[[monthly.top$top.artists[i,1]]] + 1 * 1/j
      }
    }
  }
}
result = sort(unlist(result)/max(unlist(result)), decreasing=TRUE)