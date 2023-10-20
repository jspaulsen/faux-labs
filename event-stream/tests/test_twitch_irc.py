from app.twitch_irc import RawMessage


class TestRawMessage:
    def test_parse_ping(self) -> None:
        raw = "PING :tmi.twitch.tv"
        message = RawMessage.parse_individual_raw_message(raw)

        assert message.tags is None
        assert not message.origin
        assert message.command == "PING"
        assert message.message == "tmi.twitch.tv"
    
    def test_parse_message(self) -> None:
        message = "@badge-info=subscriber/20;badges=vip/1,subscriber/18,bits/1000;color=#670070;display-name=Ginauz;emotes=;first-msg=0;flags=;id=575a24ac-0a91-48fb-b815-d62e0758c3e5;mod=0;returning-chatter=0;room-id=477536370;subscriber=1;tmi-sent-ts=1697759493254;turbo=0;user-id=73138589;user-type=;vip=1 :g!g@g.tmi.twitch.tv PRIVMSG #g :Message"
        parsed_message = RawMessage.parse_individual_raw_message(message)

        assert 'badges' in parsed_message.tags
        assert parsed_message.origin == "g!g@g.tmi.twitch.tv"
        assert parsed_message.message == "#g :Message"
        assert parsed_message.command == "PRIVMSG"
    
    def test_join_message(self) -> None:
        message = ":b!b@b.tmi.twitch.tv JOIN #g"
        parsed_message = RawMessage.parse_individual_raw_message(message)

        assert parsed_message.origin == "b!b@b.tmi.twitch.tv"
        assert parsed_message.message == "#g"
        assert parsed_message.command == "JOIN"
