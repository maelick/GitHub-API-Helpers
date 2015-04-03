library(ggplot2)
library(data.table)

source("R/plot-ts.R")

multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  library(grid)

  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)

  numPlots = length(plots)

  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                    ncol = cols, nrow = ceiling(numPlots/cols))
  }

 if (numPlots==1) {
    print(plots[[1]])

  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))

    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))

      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}

ParseGitDate <- function(time) {
  utc <- grep("Z$", time)
  time[utc] <- sub("Z$", "+0000", time[utc])
  time[-utc] <- sub(":(\\d+)$", "\\1", time[-utc])
  as.POSIXct(strptime(time, format="%Y-%m-%dT%H:%M:%S%z"))
}

Date <- function(packages, package=NULL, version=NULL, date=NULL) {
  if (is.null(date)) {
    if (!is.null(package)) {
      packages <- packages[package == package, ]
      if (!is.null(version)) packages <- packages[version == version, ]
    }
    as.Date(max(packages$mtime))
  } else as.Date(date)
}

State <- function(packages, date=Sys.Date()) {
  packages[packages[as.Date(mtime) <= date, .I[which.max(mtime)],
                    by=package]$V1]
}

packages <- fread("data/cran-packages.csv")[!is.na(mtime)]
packages[, date := strftime(mtime, "%Y-%m-%d")]
packages[, period := strftime(mtime, "%Y-%m-01")]
packages[, period2 := strftime(mtime, "%Y-01-01")]
setkey(packages, package, version)
p1 <- PlotTS(packages[, list(n=.N), by="period2"][, list(date=period2, n)])
p2 <- PlotTS(packages[, list(n=.N), by="period"][, list(date=period, n)])
p3 <- PlotTS(packages[, list(n=.N), by="date"])

packages[, list(n=.N), by="date"][n > 400]

first <- fread("data/cran-first.csv")[!is.na(mtime)]
first[, date := strftime(mtime, "%Y-%m-%d")]
first[, period := strftime(mtime, "%Y-%m-01")]
first[, period2 := strftime(mtime, "%Y-01-01")]
setkey(first, package, version)
p4 <- PlotTS(first[, list(n=.N), by="period2"][, list(date=period2, n)])
p5 <- PlotTS(first[, list(n=.N), by="period"][, list(date=period, n)])
p6 <- PlotTS(first[, list(n=.N), by="date"])

first[, list(n=.N), by="date"][n > 100]

multiplot(p1, p2, p3, p4, p5, p6, cols=2)

pdf("images/new-releases.pdf")
p1 + ylab("# updated packages") + ggtitle("# yearly updates on CRAN")
p2 + ylab("# updated packages") + ggtitle("# monthly updates on CRAN")
p3 + ylab("# updated packages") + ggtitle("# daily updates on CRAN")
p4 + ylab("# new packages") + ggtitle("# yearly new packages on CRAN")
p5 + ylab("# new packages") + ggtitle("# monthly new packages on CRAN")
p6 + ylab("# new packages") + ggtitle("# daily new packages on CRAN")
dev.off()

github <- as.data.table(read.csv("data/github-RPackage-repository.csv",
                                 stringsAsFactors=FALSE)[-1])
github <- github[, list(owner, repository, package=Package, creation,
                        last_push, fork, forks)]
github <- github[!owner %in% c("cran", "rpkg")]
github[, creation := ParseGitDate(creation)]
github[, last_push := ParseGitDate(last_push)]

github.creation <- github[, list(github=min(creation)), by="package"]
setkey(github.creation, package)

res <- github.creation[packages]
setkey(res, package, version)

# Number of releases that are now on Github
table(!is.na(res$github))
res[, on.github := mapply(function(github, cran) {
  !is.na(github) && github < cran
}, github, mtime)]

p7 <- PlotTS(res[, list(value=nrow(.SD[.SD$on.github]) / .N), by="period"][, list(date=period, value)])
p8 <- PlotTS(res[, list(value=nrow(.SD[.SD$on.github]) / .N), by="period2"][, list(date=period2, value)])
p9 <- PlotTS(res[first[, list(package, version)],
                 list(value=nrow(.SD[.SD$on.github]) / .N), by="period"][, list(date=period, value)])
p10 <- PlotTS(res[first[, list(package, version)],
                 list(value=nrow(.SD[.SD$on.github]) / .N), by="period2"][, list(date=period2, value)])

both <- sapply(sort(unique(packages$period)), function(p) {
  length(github.creation[github < p & package %in% packages$package,
                         unique(package)])
})
cran <- sapply(sort(unique(packages$period)), function(p) {
  length(packages[mtime < p, unique(package)])
})
p11 <- PlotTS(data.table(date=sort(unique(packages$period)), value=both / cran))

multiplot(p7, p9, p11, p8, p10, cols=2)

pdf("images/new-releases-relative.pdf")
p7 + ylab("% udpated packages") + ggtitle("# monthly updates on CRAN already on Github")
p8 + ylab("% updated packages") + ggtitle("# yearly updates on CRAN already on Github")
p9 + ylab("% new packages") + ggtitle("# monthly new packages on CRAN already on Github")
p10 + ylab("% new packages") + ggtitle("# yearly new packages on CRAN already on Github")
p11 + ylab("% packages") + ggtitle("% packages on CRAN and Github")
dev.off()
