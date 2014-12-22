(function(define) {
'use strict';
// VideoCommands module.
define('video/10_commands.js', [], function() {
    var VideoCommands, Command, playCommand, pauseCommand, togglePlaybackCommand,
        muteCommand, unmuteCommand, toggleMuteCommand, toggleFullScreenCommand,
        setSpeedCommand;

    /**
     * Video commands module.
     * @exports video/10_commands.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * @param {Object} i18n The object containing strings with translations.
     * @return {jquery Promise}
     */
    VideoCommands = function(state, i18n) {
        if (!(this instanceof VideoCommands)) {
            return new VideoCommands(state, i18n);
        }

        this.state = state;
        this.state.videoCommands = this;
        this.i18n = i18n;
        this.commands = [];
        this.initialize();

        return $.Deferred().resolve().promise();
    };

    VideoCommands.prototype = {
        /** Initializes the module. */
        initialize: function() {
            this.commands = this.getCommands();
        },

        execute: function (command) {
            var args = [].slice.call(arguments, 1) || [];

            if (_.has(this.commands, command)) {
                this.commands[command].execute.apply(this, [this.state].concat(args));
            } else {
                console.log('Command "' + command + '" is not available.');
            }
        },

        getCommands: function () {
            var commands = {},
                commandsList = [
                    playCommand, pauseCommand, togglePlaybackCommand,
                    toggleMuteCommand, toggleFullScreenCommand, setSpeedCommand
                ];

            _.each(commandsList, function(command) {
                commands[command.name] = command;
            }, this);

            return commands;
        }
    };

    Command = function (name, execute) {
        this.name = name;
        this.execute = execute;
    };

    playCommand = new Command('play', function (state) {
        state.videoPlayer.play();
    });

    pauseCommand = new Command('pause', function (state) {
        state.videoPlayer.pause();
    });

    togglePlaybackCommand = new Command('togglePlayback', function (state) {
        if (state.videoControl.isPlaying) {
            pauseCommand.execute(state);
        } else {
            playCommand.execute(state);
        }
    });

    toggleMuteCommand = new Command('toggleMute', function (state) {
        state.videoVolumeControl.toggleMute();
    });

    toggleFullScreenCommand = new Command('toggleFullScreen', function (state) {
        state.videoControl.toggleFullScreen();
    });

    setSpeedCommand = new Command('speed', function (state, speed) {
        state.videoSpeedControl.setSpeed(state.speedToString(speed));
    });

    return VideoCommands;
});
}(RequireJS.define));
