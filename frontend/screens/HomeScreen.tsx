import React, { useState } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Header } from '../components/ui/Header';
import { TabBar } from '../components/navigation/TabBar';
import { TimeCard } from '../components/ui/TimeCard';
import { RoomCard } from '@/components/ui/RoomCard';
import { AlarmModal, AlarmConfig } from '../components/ui/AlarmModal';

const TABS = [
  { label: 'Rooms', value: 'rooms' },
  { label: 'Products', value: 'products' },
];

const TIME_CARDS = [
  {
    id: '1',
    title: 'Rise and shine',
    subtitle: '7:00 AM · Daily',
    icon: 'sunny-outline' as const,
  },
  {
    id: '2',
    title: 'After work',
    subtitle: '6:31 PM',
    icon: 'sparkles-outline' as const,
  },
];

const ROOMS = [
  {
    id: '1',
    title: 'Entrance',
    icon: 'door-open-outline' as const,
    backgroundColor: '#E8B23E',
    hasDevice: true,
  },
  {
    id: '2',
    title: 'Other',
    icon: 'briefcase-outline' as const,
    backgroundColor: '#6B9AC4',
    hasDevice: false,
  },
  {
    id: '3',
    title: 'Study',
    icon: 'book-outline' as const,
    backgroundColor: '#9BC4E2',
    hasDevice: false,
  },
];

export const HomeScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rooms');
  const [isModalVisible, setIsModalVisible] = useState(false);

  const handleAddPress = () => {
    setIsModalVisible(true);
  };

  const handleSaveAlarm = (alarm: AlarmConfig) => {
    console.log('Alarm saved:', alarm);
    // TODO: Add alarm to state/backend
  };

  const handleRoomPress = (roomId: string) => {
    console.log('Room pressed:', roomId);
  };

  return (
    <View style={styles.container}>
      <Header title="Home" onAddPress={handleAddPress} />

      <TabBar
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.timeCardsContainer}>
          {TIME_CARDS.map(card => (
            <TimeCard
              key={card.id}
              title={card.title}
              subtitle={card.subtitle}
              icon={card.icon}
            />
          ))}
        </View>

        {activeTab === 'rooms' && (
          <View>
            {ROOMS.map(room => (
              <RoomCard
                key={room.id}
                title={room.title}
                icon={room.icon}
                backgroundColor={room.backgroundColor}
                hasDevice={room.hasDevice}
                onPress={() => handleRoomPress(room.id)}
              />
            ))}
          </View>
        )}


      <AlarmModal
        visible={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        onSave={handleSaveAlarm}
      />
        {activeTab === 'products' && (
          <View style={styles.emptyState}>
            {/* Products view can be implemented here */}
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  timeCardsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  emptyState: {
    padding: 20,
  },
});
