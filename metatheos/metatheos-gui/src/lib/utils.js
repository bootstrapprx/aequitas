export function getFileIcon(fileType) {
    switch (fileType) {
        case 'Canon':
            return '🧠'
        case 'Goal':
            return '🎯'
        case 'Phase':
            return '🧭'
        case 'Decision':
            return '⚖'
        case 'Audit':
            return '🧪'
        case 'Prompt':
            return '💡'
        case 'Daily':
            return '📝'
        case 'Archive':
            return '📦'
        case 'Constitution':
            return '📜'
        case 'Directory':
            return '📁'
        default:
            return '📄'
    }
}

export function getBadgeClass(fileType, isWritable) {
    if (!isWritable) {
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
    }

    switch (fileType) {
        case 'Canon':
        case 'Constitution':
            return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
        case 'Goal':
            return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
        case 'Phase':
            return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
        case 'Decision':
            return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
        case 'Audit':
            return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
        case 'Prompt':
            return 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
        case 'Daily':
            return 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300'
        default:
            return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }
}
