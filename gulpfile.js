'use strict';

// Gulp && plugins
var gulp = require('gulp');

var cleanCSS = require('gulp-clean-css');
var sass     = require('gulp-sass');
var concat   = require('gulp-concat');
var minify   = require('gulp-minify');


var vendor_js = [
    './node_modules/jquery/dist/jquery.js',
    './node_modules/bootstrap-sass/assets/javascripts/bootstrap.js',
];


gulp.task('vendor', function() {
	// javascripts
    gulp.src(vendor_js)
        .pipe(concat('vendor.js'))
        .pipe(minify({
                ext:{
                    src:'.js',
                    min:'.min.js'
                },
                compress: {
                    properties: false
                },
            }))
        .pipe(gulp.dest('./admin/static/js'));

    // bootstrap-sass
    gulp.src('./node_modules/bootstrap-sass/assets/stylesheets/**/*.scss')
        .pipe(gulp.dest('./admin/sass/vendor'));
    gulp.src('./node_modules/bootstrap-sass/assets/fonts/bootstrap/*.{ttf,svg,eot,woff,woff2}')
        .pipe(gulp.dest('./admin/static/fonts/bootstrap'));

	// font roboto
    gulp.src('./node_modules/roboto-fontface/css/**/*.scss')
        .pipe(gulp.dest('./admin/sass/vendor/roboto'));
    gulp.src('./node_modules/roboto-fontface/fonts/**/*.{ttf,svg,eot,woff,woff2,otf}')
        .pipe(gulp.dest('./admin/static/fonts'));

	// font roboto slab
    gulp.src('./node_modules/roboto-slab-fontface-kit/sass/*.scss')
        .pipe(gulp.dest('./admin/sass/vendor/roboto-slab'));
    gulp.src('./node_modules/roboto-slab-fontface-kit/fonts/**/*.{ttf,svg,eot,woff,woff2,otf}')
        .pipe(gulp.dest('./admin/static/fonts/roboto-slab'));

    // material-design-icons
    gulp.src('./node_modules/mdi/scss/*.scss')
        .pipe(gulp.dest('./admin/sass/vendor/mdi'));
    gulp.src('./node_modules/mdi/fonts/*.{ttf,svg,eot,woff,woff2,otf}')
        .pipe(gulp.dest('./admin/static/fonts'));
});


gulp.task('sass', function() {
    gulp.src('./admin/sass/main.scss')
        .pipe(sass.sync().on('error', sass.logError))
        .pipe(cleanCSS())
        .pipe(gulp.dest('./admin/static/css'));
});


gulp.task('js', function() {
//    gulp.src('./src/js/*.js')
//          .pipe(gulp.dest('./dist/js'));
//        .pipe(minify({
//                ext:{
//                    src:'.js',
//                    min:'.min.js'
//                },
//                compress: {
//                    properties: false
//                },
//            }))
//        .pipe(gulp.dest('./dist/js'));
});


// Watch it, Gulp!
gulp.task('watch', function ()
{
    gulp.watch('./admin/sass/*.scss', ['sass']);
    gulp.watch('./admin/js/*.js', ['js']);
});

